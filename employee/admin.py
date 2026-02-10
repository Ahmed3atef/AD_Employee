import re
import logging

from django.contrib import admin, messages
from django.contrib.admin.models import LogEntry, ADDITION
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import path
from django.utils import timezone

from . import models

logger = logging.getLogger(__name__)
User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_clean_ldap_val(entry, attr_name):
    """Extract a clean string value from an LDAP entry attribute."""
    val = getattr(entry, attr_name, None)
    if not val or val == [] or str(val).strip() == "":
        return None
    if isinstance(val, list):
        return str(val[0]).strip()
    return str(val).strip()


def extract_ou_from_dn(dn):
    """Return the first OU component from a Distinguished Name, or None."""
    match = re.search(r'OU=([^,]+)', dn or "")
    return match.group(1).strip() if match else None


def get_ad_connection(request):
    """
    Retrieve cached AD credentials and return an authenticated AD connection.
    Returns (ad_connection, error_message).  On success error_message is None.
    """
    creds = cache.get(f'ad_creds_{request.user.id}')
    if not creds or not creds.get('username') or not creds.get('password'):
        return None, "Credentials not found in cache. Please re-login."

    ad = settings.ACTIVE_DIR
    if not ad.connect_ad(creds['username'], creds['password']):
        return None, "Failed to connect to AD with your credentials."

    return ad, None


def get_client_ip(request):
    """Get the client IP address from the request."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ---------------------------------------------------------------------------
# Simple model registrations
# ---------------------------------------------------------------------------

admin.site.register(models.Job)
admin.site.register(models.Department)


# ---------------------------------------------------------------------------
# OUTransferLog Admin
# ---------------------------------------------------------------------------

@admin.register(models.OUTransferLog)
class OUTransferLogAdmin(admin.ModelAdmin):
    list_display = (
        'employee_username', 'employee_display_name',
        'old_ou', 'new_ou', 'status', 'database_updated',
        'performed_by', 'timestamp',
    )
    list_filter = ('status', 'database_updated', 'timestamp', 'performed_by')
    search_fields = ('employee_username', 'employee_display_name', 'old_ou', 'new_ou')
    readonly_fields = (
        'performed_by', 'employee', 'employee_username', 'employee_display_name',
        'old_ou', 'new_ou', 'old_dn', 'new_dn', 'database_updated',
        'old_department', 'new_department', 'status', 'error_message',
        'ip_address', 'timestamp',
    )
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ---------------------------------------------------------------------------
# Employee Admin
# ---------------------------------------------------------------------------

@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'full_name_en', 'full_name_ar',
        'hire_date', 'nid', 'job_title', 'department',
    )
    list_filter = ('job_title', 'department')
    search_fields = ('user__username', 'full_name_en', 'full_name_ar')
    ordering = ('full_name_en',)

    # ------------------------------------------------------------------
    # Custom URLs
    # ------------------------------------------------------------------

    def get_urls(self):
        custom_urls = [
            path(
                'sync-users/',
                self.admin_site.admin_view(self.sync_users_view),
                name='sync_users_action',
            ),
            path(
                'transfer-ou/',
                self.admin_site.admin_view(self.transfer_ou_view),
                name='transfer_ou_page',
            ),
        ]
        return custom_urls + super().get_urls()

    # ------------------------------------------------------------------
    # Sync Users from AD
    # ------------------------------------------------------------------

    def sync_users_view(self, request):
        """Pull users from AD and sync to local DB — idempotent."""
        ad, error = get_ad_connection(request)
        if error:
            self.message_user(request, error, level=messages.ERROR)
            return redirect("admin:index")

        entries = ad.get_all_users_full_info(
            attributes=['sAMAccountName', 'displayName', 'title'],
        )

        sync_count = 0

        with transaction.atomic():
            for entry in entries:
                sam = get_clean_ldap_val(entry, 'sAMAccountName')
                if not sam:
                    continue

                ad_username = sam.lower()
                display_name = get_clean_ldap_val(entry, 'displayName')
                job_title_str = get_clean_ldap_val(entry, 'title')

                # --- Resolve department from DN ---
                dn = getattr(entry, 'entry_dn', "")
                dept_name = extract_ou_from_dn(dn)
                dept_obj = (
                    models.Department.objects.filter(name__iexact=dept_name).first()
                    if dept_name else None
                )

                # --- Resolve job title ---
                job_obj = None
                if job_title_str:
                    job_obj, _ = models.Job.objects.get_or_create(title=job_title_str)

                # --- Get or create the auth User ---
                full_username = f'{ad_username}@{settings.DOMAIN}'
                user_obj, _ = User.objects.get_or_create(
                    username=full_username,
                    defaults={'is_active': True, 'is_staff': False},
                )

                # --- Check if Employee already exists with identical data ---
                try:
                    existing = models.Employee.objects.get(user=user_obj)
                    # Compare current DB values with incoming AD values
                    if (
                        existing.full_name_en == display_name
                        and existing.department_id == (dept_obj.id if dept_obj else None)
                        and existing.job_title_id == (job_obj.id if job_obj else None)
                    ):
                        # Nothing changed — skip
                        continue

                    # Something changed — update
                    existing.full_name_en = display_name
                    existing.department = dept_obj
                    existing.job_title = job_obj
                    existing.save(update_fields=['full_name_en', 'department', 'job_title'])
                    sync_count += 1

                except models.Employee.DoesNotExist:
                    # Brand-new employee
                    models.Employee.objects.create(
                        user=user_obj,
                        full_name_en=display_name,
                        department=dept_obj,
                        job_title=job_obj,
                    )
                    sync_count += 1

        self.message_user(
            request,
            f"Successfully synced {sync_count} users. Departments matched from DN.",
        )
        return redirect("admin:index")

    # ------------------------------------------------------------------
    # Transfer OU  (GET = search, POST = transfer)
    # ------------------------------------------------------------------

    def transfer_ou_view(self, request):
        """Handle user search (GET) and OU transfer (POST)."""
        ad, error = get_ad_connection(request)
        if error:
            self.message_user(request, error, level=messages.ERROR)
            return redirect("admin:index")

        context = self._build_transfer_context(request)

        if request.method == 'POST':
            return self._handle_transfer_post(request, ad, context)

        return self._handle_transfer_get(request, ad, context)

    # ---- context builder ----

    def _build_transfer_context(self, request):
        """Build the shared context dict for the transfer OU page."""
        audit_qs = models.OUTransferLog.objects.select_related(
            'performed_by', 'employee', 'old_department', 'new_department',
        ).all()

        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0)
        stats = {
            'total': audit_qs.count(),
            'success': audit_qs.filter(status='success').count(),
            'failed': audit_qs.filter(status='failed').count(),
            'this_month': audit_qs.filter(timestamp__gte=month_start).count(),
        }

        paginator = Paginator(audit_qs, 20)
        page = request.GET.get('page', 1)

        return {
            **self.admin_site.each_context(request),
            'title': 'Transfer OU',
            'departments': models.Department.objects.order_by('name'),
            'audit_logs': paginator.get_page(page),
            'stats': stats,
        }

    # ---- GET handler ----

    def _handle_transfer_get(self, request, ad, context):
        """Search for a user in AD and populate context."""
        search_username = request.GET.get('username', '').strip()
        if not search_username:
            return render(request, 'admin/transfer_ou.html', context)

        clean_username = search_username.split('@')[0]
        entries = ad.search_user_full_info(
            clean_username,
            attributes=['sAMAccountName', 'displayName', 'title', 'distinguishedName'],
        )

        if not entries:
            self.message_user(
                request,
                f"User '{search_username}' not found in Active Directory.",
                level=messages.ERROR,
            )
            context['username'] = search_username
            return render(request, 'admin/transfer_ou.html', context)

        entry = entries[0]
        dn = get_clean_ldap_val(entry, 'distinguishedName') or entry.entry_dn
        current_ou = extract_ou_from_dn(dn) or "Unknown"

        # Try fetching DB info
        db_dept, db_job = None, None
        user_obj = User.objects.filter(username__icontains=clean_username).first()
        if user_obj and hasattr(user_obj, 'employee_profile'):
            emp = user_obj.employee_profile
            db_dept = emp.department.name if emp.department else None
            db_job = emp.job_title.title if emp.job_title else None

        context['user_info'] = {
            'username': get_clean_ldap_val(entry, 'sAMAccountName') or clean_username,
            'display_name': get_clean_ldap_val(entry, 'displayName') or 'N/A',
            'current_ou': current_ou,
            'dn': dn,
            'job_title': db_job or get_clean_ldap_val(entry, 'title'),
            'department': db_dept or current_ou,
        }
        context['username'] = search_username
        return render(request, 'admin/transfer_ou.html', context)

    # ---- POST handler ----

    def _handle_transfer_post(self, request, ad, context):
        """Execute the OU transfer and create audit log."""
        target_username = request.POST.get('username', '').strip()
        new_ou = request.POST.get('new_ou', '').strip()
        update_db = request.POST.get('update_db') == 'on'
        old_ou = request.POST.get('current_ou', '').strip()
        old_dn = request.POST.get('current_dn', '').strip()
        display_name = request.POST.get('display_name', '').strip()

        if not target_username or not new_ou:
            self.message_user(request, "Username and OU are required.", level=messages.ERROR)
            return render(request, 'admin/transfer_ou.html', context)

        clean_username = target_username.split('@')[0]

        # Resolve DB objects
        employee_obj, old_dept_obj, new_dept_obj = None, None, None
        user_obj = User.objects.filter(username__icontains=clean_username).first()
        if user_obj and hasattr(user_obj, 'employee_profile'):
            employee_obj = user_obj.employee_profile
            old_dept_obj = employee_obj.department

        transfer_status = 'failed'
        error_msg = None
        new_dn = None

        try:
            success = ad.update_ou(clean_username, new_ou)

            if success:
                new_dn = self._build_new_dn(old_dn, new_ou)

                if update_db:
                    transfer_status, error_msg, new_dept_obj = self._update_db_department(
                        request, employee_obj, target_username, new_ou,
                    )
                else:
                    transfer_status = 'success'
                    self.message_user(
                        request,
                        f"Successfully transferred {target_username} to {new_ou} in Active Directory.",
                        level=messages.SUCCESS,
                    )
            else:
                error_msg = "AD transfer operation failed"
                self.message_user(
                    request,
                    f"Failed to transfer {target_username}. Check logs for details.",
                    level=messages.ERROR,
                )
        except Exception as exc:
            error_msg = str(exc)
            self.message_user(request, f"Error during transfer: {exc}", level=messages.ERROR)

        self._create_audit_log(
            request=request,
            username=clean_username,
            display_name=display_name,
            old_ou=old_ou,
            new_ou=new_ou,
            old_dn=old_dn,
            new_dn=new_dn,
            status=transfer_status,
            database_updated=update_db and transfer_status in ('success', 'partial'),
            old_dept=old_dept_obj,
            new_dept=new_dept_obj,
            employee=employee_obj,
            error_message=error_msg,
        )

        return redirect('admin:transfer_ou_page')

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_new_dn(old_dn, new_ou):
        """Construct the new DN after an OU transfer."""
        cn_match = re.match(r'CN=([^,]+)', old_dn or "")
        if not cn_match:
            return None
        cn = cn_match.group(1)
        return f"CN={cn},OU={new_ou},{settings.CONTAINER_DN_BASE}"

    def _update_db_department(self, request, employee_obj, target_username, new_ou):
        """
        Update the employee's department in the DB after an AD transfer.
        Returns (status, error_message, new_dept_obj).
        """
        if not employee_obj:
            self.message_user(
                request,
                f"Transferred in AD but user not found in database. Run 'Sync Users' to update.",
                level=messages.WARNING,
            )
            return 'partial', "User not found in database", None

        new_dept_obj = models.Department.objects.filter(name__iexact=new_ou).first()

        if not new_dept_obj:
            self.message_user(
                request,
                f"Transferred in AD but department '{new_ou}' not found in database. Please create it first.",
                level=messages.WARNING,
            )
            return 'partial', f"Department '{new_ou}' not found in database", None

        try:
            employee_obj.department = new_dept_obj
            employee_obj.save(update_fields=['department'])
            self.message_user(
                request,
                f"Successfully transferred {target_username} to {new_ou} in both AD and database.",
                level=messages.SUCCESS,
            )
            return 'success', None, new_dept_obj
        except Exception as exc:
            self.message_user(
                request,
                f"Transferred in AD but database update failed: {exc}",
                level=messages.WARNING,
            )
            return 'partial', str(exc), None

    def _create_audit_log(self, *, request, username, display_name, old_ou, new_ou,
                          old_dn, new_dn, status, database_updated,
                          old_dept=None, new_dept=None, employee=None,
                          error_message=None):
        """Create an OUTransferLog entry and a Django admin LogEntry."""
        log = models.OUTransferLog.objects.create(
            performed_by=request.user,
            employee=employee,
            employee_username=username,
            employee_display_name=display_name,
            old_ou=old_ou,
            new_ou=new_ou,
            old_dn=old_dn,
            new_dn=new_dn,
            database_updated=database_updated,
            old_department=old_dept,
            new_department=new_dept,
            status=status,
            error_message=error_message,
            ip_address=get_client_ip(request),
        )

        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(models.OUTransferLog).pk,
            object_id=log.pk,
            object_repr=f"{display_name or username}: {old_ou} → {new_ou}",
            action_flag=ADDITION,
            change_message=f"OU Transfer: {old_ou} → {new_ou} ({status})",
        )

        return log