import logging
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import path
from .utils import _get_ad_creds, _connect_ad
from .forms import ADUserCreationForm, ADPasswordChangeForm
from .models import User

logger = logging.getLogger(__name__)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username',)
    ordering = ('username',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'is_active', 'is_staff'),
        }),
    )

    filter_horizontal = ('groups', 'user_permissions')

    def has_add_permission(self, request):
        return False

    def get_urls(self):
        custom_urls = [
            path(
                'create-ad-user/',
                self.admin_site.admin_view(self.create_ad_user_view),
                name='create_ad_user',
            ),
            path(
                '<path:object_id>/change-ad-password/',
                self.admin_site.admin_view(self.change_ad_password_view),
                name='change_ad_password',
            ),
            path(
                '<path:object_id>/delete-ad-user/',
                self.admin_site.admin_view(self.delete_ad_user),
                name='delete_ad_user'
            )
        ]
        return custom_urls + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_create_ad_user_button'] = True
        return super().changelist_view(request, extra_context=extra_context)

    # ------------------------------------------------------------------
    # Create AD User View
    # ------------------------------------------------------------------

    def create_ad_user_view(self, request):
        creds = _get_ad_creds(request)
        if not creds:
            messages.error(request, "AD credentials not found in cache. Please re-login.")
            return redirect('admin:core_user_changelist')

        if request.method == 'POST':
            form = ADUserCreationForm(request.POST)
            if form.is_valid():
                return self._process_ad_user_creation(request, form, creds)
        else:
            form = ADUserCreationForm()

        context = {
            **self.admin_site.each_context(request),
            'title': 'Create AD User',
            'form': form,
            'opts': self.model._meta,
        }
        return render(request, 'admin/create_ad_user.html', context)

    def _process_ad_user_creation(self, request, form, creds):
        username = form.cleaned_data['username'].strip().lower()
        password = form.cleaned_data['password']
        given_name = form.cleaned_data['given_name'].strip()
        surname = form.cleaned_data['surname'].strip()
        email = form.cleaned_data['email'] or f"{username}@{settings.DOMAIN}"
        telephone = form.cleaned_data['telephone']
        ou_dept = form.cleaned_data['ou']
        ou_name = ou_dept.name if ou_dept else None

        ad = _connect_ad(creds)
        if not ad:
            messages.error(request, "Failed to connect to Active Directory.")
            return redirect('admin:create_ad_user')

        success, msg = ad.create_user(
            username=username, password=password,
            given_name=given_name, surname=surname,
            mail=email, telephone=telephone, ou=ou_name,
        )

        if success:
            messages.success(request, f"✓ {msg}")
            logger.info(f"Admin {request.user.username} created AD user: {username}")
        else:
            messages.error(request, f"Failed to create AD user: {msg}")
            return redirect('admin:create_ad_user')

        return redirect('admin:core_user_changelist')

    # ------------------------------------------------------------------
    # Change AD Password View
    # ------------------------------------------------------------------

    def change_ad_password_view(self, request, object_id):
        """Change a user's password directly in Active Directory."""
        try:
            user_obj = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('admin:core_user_changelist')

        # Extract sAMAccountName (strip @domain)
        ad_username = user_obj.username.split('@')[0]

        creds = _get_ad_creds(request)
        if not creds:
            messages.error(request, "AD credentials not found in cache. Please re-login.")
            return redirect('admin:core_user_change', object_id)

        if request.method == 'POST':
            form = ADPasswordChangeForm(request.POST)
            if form.is_valid():
                return self._process_password_change(
                    request, form, creds, ad_username, object_id,
                )
        else:
            form = ADPasswordChangeForm()

        context = {
            **self.admin_site.each_context(request),
            'title': f'Change AD Password — {ad_username}',
            'form': form,
            'ad_username': ad_username,
            'user_obj': user_obj,
            'opts': self.model._meta,
        }
        return render(request, 'admin/change_ad_password.html', context)

    def _process_password_change(self, request, form, creds, ad_username, object_id):
        new_password = form.cleaned_data['new_password']

        ad = _connect_ad(creds)
        if not ad:
            messages.error(request, "Failed to connect to Active Directory.")
            return redirect('admin:change_ad_password', object_id=object_id)

        success, msg = ad.change_password(ad_username, new_password)

        if success:
            messages.success(request, f"✓ {msg}")
            logger.info(
                f"Admin {request.user.username} changed AD password for: {ad_username}"
            )
            return redirect('admin:core_user_change', object_id)
        else:
            messages.error(request, f"Failed to change password: {msg}")
            return redirect('admin:change_ad_password', object_id=object_id)
        
    # ------------------------------------------------------------------
    # Delete AD User View
    # ------------------------------------------------------------------

    def delete_ad_user(self, request, object_id):
        """Delete a user from Active Directory and the local database."""
        try:
            user_obj = User.objects.get(pk=object_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect('admin:core_user_changelist')

        ad_username = user_obj.username.split('@')[0]

        creds = _get_ad_creds(request)
        if not creds:
            messages.error(request, "AD credentials not found in cache. Please re-login.")
            return redirect('admin:core_user_change', object_id)

        if request.method == 'POST':
            return self._process_ad_user_deletion(request, creds, user_obj, ad_username)

        # GET — show confirmation page
        context = {
            **self.admin_site.each_context(request),
            'title': f'Delete AD User — {ad_username}',
            'ad_username': ad_username,
            'user_obj': user_obj,
            'opts': self.model._meta,
        }
        return render(request, 'admin/delete_ad_user.html', context)

    def _process_ad_user_deletion(self, request, creds, user_obj, ad_username):
        """Delete user from AD, then remove Employee + User from DB."""
        ad = _connect_ad(creds)
        if not ad:
            messages.error(request, "Failed to connect to Active Directory.")
            return redirect('admin:core_user_change', user_obj.pk)

        # 1. Delete from Active Directory
        success, msg = ad.delete_user(ad_username)
        if not success:
            messages.error(request, f"Failed to delete from AD: {msg}")
            return redirect('admin:core_user_change', user_obj.pk)

        # 2. Delete Employee profile from DB (if exists)
        if hasattr(user_obj, 'employee_profile'):
            user_obj.employee_profile.delete()

        # 3. Delete the Django User from DB
        username_display = user_obj.username
        user_obj.delete()

        messages.success(
            request,
            f"✓ User '{ad_username}' deleted from Active Directory and database.",
        )
        logger.info(
            f"Admin {request.user.username} deleted AD user: {ad_username} ({username_display})"
        )
        return redirect('admin:core_user_changelist')