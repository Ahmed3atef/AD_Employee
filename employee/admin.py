import re, os
from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import redirect, render
from django.db import transaction
from . import models
from core.ad_conn import ADConnection  
from django.contrib.auth import get_user_model

User = get_user_model()

admin.site.register(models.Job)
admin.site.register(models.Department)

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
    
    def transfer_ou_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Transfer OU",
        }
        return render(request, 'admin/transfer_ou.html', context)
    
