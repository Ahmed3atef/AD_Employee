import re, os
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from datetime import datetime, timedelta
from . import models
from core.ad_conn import ADConnection  
from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(models.Job)
admin.site.register(models.Department)

@admin.register(models.OUTransferLog)
class OUTransferLogAdmin(admin.ModelAdmin):
    list_display = ('employee_username', 'employee_display_name', 'old_ou', 'new_ou', 
                    'status', 'database_updated', 'performed_by', 'timestamp')
    list_filter = ('status', 'database_updated', 'timestamp', 'performed_by')
    search_fields = ('employee_username', 'employee_display_name', 'old_ou', 'new_ou')
    readonly_fields = ('performed_by', 'employee', 'employee_username', 'employee_display_name',
                       'old_ou', 'new_ou', 'old_dn', 'new_dn', 'database_updated',
                       'old_department', 'new_department', 'status', 'error_message',
                       'ip_address', 'timestamp')
    ordering = ('-timestamp',)
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Logs are created automatically, not manually
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete audit logs
        return request.user.is_superuser


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name_en', 'full_name_ar', 'hire_date', 'nid', 'job_title', 'department')
    list_filter = ('job_title', 'department')
    search_fields = ('user__username', 'full_name_en', 'full_name_ar')
    ordering = ('full_name_en',)
    
    def get_urls(self):
        """Register custom URLs within the Admin class."""
        
        urls = super().get_urls()
        custom_urls = [
            path('sync-users/', self.admin_site.admin_view(self.sync_users_action), name='sync_users_action'),
            path('transfer-ou/', self.admin_site.admin_view(self.transfer_ou_view), name='transfer_ou_page'),
        ]
        return custom_urls + urls
    
    def sync_users_action(self, request):
        username = request.session.get('ad_user')
        password = request.session.get('ad_password')

        if not username or not password:
            self.message_user(request, "Credentials not found in session. Please re-login.", level=messages.ERROR)
            return redirect("admin:index")

        ad = ADConnection()
        if not ad.connect_ad(username, password):
            self.message_user(request, "Failed to connect to AD with your credentials.", level=messages.ERROR)
            return redirect("admin:index")

        # Fetch entries
        entries = ad.get_all_users_full_info(attributes=['sAMAccountName', 'displayName', 'title'])
        
        sync_count = 0
        with transaction.atomic():
            for entry in entries:
                if not hasattr(entry, 'sAMAccountName'):
                    continue

                # 1. Robust Data Cleaner
                def get_clean_val(attr_name):
                    val = getattr(entry, attr_name, None)
                    # If LDAP returns an empty list [], None, or empty string, return None
                    if not val or val == [] or str(val).strip() == "":
                        return None
                    # If it's a list (common in LDAP), take the first item
                    if isinstance(val, list):
                        return str(val[0]).strip()
                    return str(val).strip()

                # 2. Parse Department from DN (e.g., CN=...,OU=Accountant,OU=New,...)
                # We look for the first occurrence of OU=
                dept_obj = None
                dn = getattr(entry, 'entry_dn', "")
                ou_match = re.search(r'OU=([^,]+)', dn) # Captures the first OU value before the next comma
                
                if ou_match:
                    dept_name = ou_match.group(1).strip()
                    # Per your requirement: Select only, do not create
                    dept_obj = models.Department.objects.filter(name__iexact=dept_name).first()

                # 3. Get or Create Job (using cleaner)
                job_title_str = get_clean_val('title')
                job_obj = None
                if job_title_str:
                    job_obj, _ = models.Job.objects.get_or_create(title=job_title_str)

                # 4. Sync User
                ad_username = get_clean_val('sAMAccountName').lower()
                user_obj, _ = User.objects.get_or_create(
                    username=f'{ad_username}@{os.getenv('AD_DOMAIN')}',
                    defaults={'is_active': True, 'is_staff': False}
                )

                # 5. Update/Create Employee Profile
                # If dept_obj or job_obj is None, Django sets the field to NULL
                models.Employee.objects.update_or_create(
                    user=user_obj,
                    defaults={
                        'full_name_en': get_clean_val('displayName'),
                        'department': dept_obj,
                        'job_title': job_obj,
                    }
                )
                sync_count += 1

        self.message_user(request, f"Successfully synced {sync_count} users. Departments matched from DN.")
        return redirect("admin:index")
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def create_audit_log(self, request, username, display_name, old_ou, new_ou, 
                        old_dn, new_dn, status, database_updated, 
                        old_dept=None, new_dept=None, employee=None, error_message=None):
        """Create an audit log entry and Django admin log entry"""
        
        # Create OUTransferLog
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
            ip_address=self.get_client_ip(request)
        )
        
        # Create Django admin LogEntry for Recent Actions
        LogEntry.objects.log_action(
            user_id=request.user.pk,
            content_type_id=ContentType.objects.get_for_model(models.OUTransferLog).pk,
            object_id=log.pk,
            object_repr=f"{display_name or username}: {old_ou} → {new_ou}",
            action_flag=ADDITION,
            change_message=f"OU Transfer: {old_ou} → {new_ou} ({status})"
        )
        
        return log
    
    def transfer_ou_view(self, request):
        """Handle both GET (search) and POST (transfer) for Transfer OU page"""
        
        # Get AD credentials from session
        username = request.session.get('ad_user')
        password = request.session.get('ad_password')

        if not username or not password:
            self.message_user(request, "Credentials not found in session. Please re-login.", level=messages.ERROR)
            return redirect("admin:index")

        # Initialize AD connection
        ad = ADConnection()
        if not ad.connect_ad(username, password):
            self.message_user(request, "Failed to connect to AD with your credentials.", level=messages.ERROR)
            return redirect("admin:index")

        # Get audit logs with pagination
        audit_logs_list = models.OUTransferLog.objects.select_related(
            'performed_by', 'employee', 'old_department', 'new_department'
        ).all()
        
        # Calculate statistics
        stats = {
            'total': audit_logs_list.count(),
            'success': audit_logs_list.filter(status='success').count(),
            'failed': audit_logs_list.filter(status='failed').count(),
            'this_month': audit_logs_list.filter(
                timestamp__gte=timezone.now().replace(day=1, hour=0, minute=0, second=0)
            ).count(),
        }
        
        # Pagination
        paginator = Paginator(audit_logs_list, 20)  # 20 records per page
        page_number = request.GET.get('page', 1)
        audit_logs = paginator.get_page(page_number)

        context = {
            **self.admin_site.each_context(request),
            "title": "Transfer OU",
            "departments": models.Department.objects.all().order_by('name'),
            "audit_logs": audit_logs,
            "stats": stats,
        }

        # Handle POST request (Transfer action)
        if request.method == 'POST':
            target_username = request.POST.get('username', '').strip()
            new_ou = request.POST.get('new_ou', '').strip()
            update_db = request.POST.get('update_db') == 'on'
            old_ou = request.POST.get('current_ou', '').strip()
            old_dn = request.POST.get('current_dn', '').strip()
            display_name = request.POST.get('display_name', '').strip()

            if not target_username or not new_ou:
                self.message_user(request, "Username and OU are required.", level=messages.ERROR)
                return render(request, 'admin/transfer_ou.html', context)

            # Clean username (remove @domain if present)
            clean_username = target_username.split('@')[0]
            
            # Variables for audit log
            employee_obj = None
            old_dept_obj = None
            new_dept_obj = None
            transfer_status = 'failed'
            error_msg = None
            new_dn = None

            try:
                # Find employee in database
                user_obj = User.objects.filter(username__icontains=clean_username).first()
                if user_obj and hasattr(user_obj, 'employee_profile'):
                    employee_obj = user_obj.employee_profile
                    old_dept_obj = employee_obj.department
                
                # Perform the OU transfer in Active Directory
                success = ad.update_ou(clean_username, new_ou)
                
                if success:
                    # Construct new DN
                    cn_match = re.match(r'CN=([^,]+)', old_dn)
                    if cn_match:
                        cn = cn_match.group(1)
                        base_container = os.getenv('AD_CONTAINER_DN_BASE')
                        new_dn = f"CN={cn},OU={new_ou},{base_container}"
                    
                    # Update database if requested
                    if update_db:
                        try:
                            if employee_obj:
                                # Find the department
                                new_dept_obj = models.Department.objects.filter(name__iexact=new_ou).first()
                                
                                if new_dept_obj:
                                    employee_obj.department = new_dept_obj
                                    employee_obj.save()
                                    transfer_status = 'success'
                                    
                                    self.message_user(
                                        request, 
                                        f"Successfully transferred {target_username} to {new_ou} in both AD and database.",
                                        level=messages.SUCCESS
                                    )
                                else:
                                    transfer_status = 'partial'
                                    error_msg = f"Department '{new_ou}' not found in database"
                                    self.message_user(
                                        request, 
                                        f"Transferred in AD but department '{new_ou}' not found in database. Please create it first.",
                                        level=messages.WARNING
                                    )
                            else:
                                transfer_status = 'partial'
                                error_msg = "User not found in database"
                                self.message_user(
                                    request, 
                                    f"Transferred in AD but user not found in database. Run 'Sync Users' to update.",
                                    level=messages.WARNING
                                )
                        except Exception as db_error:
                            transfer_status = 'partial'
                            error_msg = str(db_error)
                            self.message_user(
                                request, 
                                f"Transferred in AD but database update failed: {str(db_error)}",
                                level=messages.WARNING
                            )
                    else:
                        transfer_status = 'success'
                        self.message_user(
                            request, 
                            f"Successfully transferred {target_username} to {new_ou} in Active Directory.",
                            level=messages.SUCCESS
                        )
                else:
                    error_msg = "AD transfer operation failed"
                    self.message_user(
                        request, 
                        f"Failed to transfer {target_username}. Check logs for details.",
                        level=messages.ERROR
                    )
                    
            except Exception as e:
                error_msg = str(e)
                self.message_user(
                    request, 
                    f"Error during transfer: {str(e)}",
                    level=messages.ERROR
                )
            
            # Create audit log
            self.create_audit_log(
                request=request,
                username=clean_username,
                display_name=display_name,
                old_ou=old_ou,
                new_ou=new_ou,
                old_dn=old_dn,
                new_dn=new_dn,
                status=transfer_status,
                database_updated=update_db and transfer_status in ['success', 'partial'],
                old_dept=old_dept_obj,
                new_dept=new_dept_obj,
                employee=employee_obj,
                error_message=error_msg
            )
            
            # Redirect to audit tab to show the new log
            return redirect('admin:transfer_ou_page')

        # Handle GET request (Search for user)
        search_username = request.GET.get('username', '').strip()
        
        if search_username:
            # Clean username
            clean_username = search_username.split('@')[0]
            
            # Search in AD
            entries = ad.search_user_full_info(
                clean_username, 
                attributes=['sAMAccountName', 'displayName', 'title', 'distinguishedName']
            )
            
            if entries and len(entries) > 0:
                entry = entries[0]
                
                # Helper function to get clean values
                def get_clean_val(attr_name):
                    val = getattr(entry, attr_name, None)
                    if not val or val == [] or str(val).strip() == "":
                        return None
                    if isinstance(val, list):
                        return str(val[0]).strip()
                    return str(val).strip()
                
                # Extract current OU from DN
                dn = get_clean_val('distinguishedName') or entry.entry_dn
                current_ou = "Unknown"
                ou_match = re.search(r'OU=([^,]+)', dn)
                if ou_match:
                    current_ou = ou_match.group(1).strip()
                
                # Try to get database info
                db_dept = None
                db_job = None
                try:
                    user_obj = User.objects.filter(username__icontains=clean_username).first()
                    if user_obj and hasattr(user_obj, 'employee_profile'):
                        employee = user_obj.employee_profile
                        db_dept = employee.department.name if employee.department else None
                        db_job = employee.job_title.title if employee.job_title else None
                except Exception:
                    pass
                
                context['user_info'] = {
                    'username': get_clean_val('sAMAccountName') or clean_username,
                    'display_name': get_clean_val('displayName') or 'N/A',
                    'current_ou': current_ou,
                    'dn': dn,
                    'job_title': db_job or get_clean_val('title'),
                    'department': db_dept or current_ou,
                }
                context['username'] = search_username
            else:
                self.message_user(
                    request, 
                    f"User '{search_username}' not found in Active Directory.",
                    level=messages.ERROR
                )
                context['username'] = search_username

        return render(request, 'admin/transfer_ou.html', context)