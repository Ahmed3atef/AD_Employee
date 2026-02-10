import logging

from django import forms
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.conf import settings
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.urls import path

from employee import models as emp_models
from .models import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Forms
# ---------------------------------------------------------------------------

class ADUserCreationForm(forms.Form):
    """
    Form to create a new user in Active Directory from the admin panel.
    The password is sent to AD only — it is NOT stored locally.
    """
    username = forms.CharField(
        max_length=100,
        help_text='sAMAccountName (e.g. ahmed.atef). Do NOT include @domain.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. ahmed.atef',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Min 7 chars, uppercase + number recommended',
        }),
        help_text='Password for the AD account. Must meet AD complexity requirements.',
    )
    given_name = forms.CharField(
        max_length=100,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Ahmed',
        }),
    )
    surname = forms.CharField(
        max_length=100,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Atef',
        }),
    )
    email = forms.EmailField(
        required=False,
        help_text='Email address (optional). Auto-generated as username@domain if left blank.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. ahmed.atef@eissa.local',
        }),
    )
    telephone = forms.CharField(
        max_length=30,
        required=False,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. 110067',
        }),
    )
    ou = forms.ModelChoiceField(
        queryset=emp_models.Department.objects.all().order_by('name'),
        required=False,
        label='Organizational Unit',
        help_text='Select the department/OU to place the user in.',
        empty_label='-- Select OU (optional) --',
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        }),
    )


class ADPasswordChangeForm(forms.Form):
    """
    Form to change a user's password in Active Directory.
    The password is sent to AD only — it is NOT stored locally.
    """
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password',
        }),
        help_text='Must meet AD complexity requirements (min 7 chars, mix of uppercase, lowercase, numbers).',
    )
    confirm_password = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password',
        }),
    )

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get('new_password')
        confirm = cleaned.get('confirm_password')
        if pwd and confirm and pwd != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ad_creds(request):
    """Return cached AD creds or None."""
    creds = cache.get(f'ad_creds_{request.user.id}')
    if not creds or not creds.get('username') or not creds.get('password'):
        return None
    return creds


def _connect_ad(creds):
    """Return an authenticated AD connection, or None on failure."""
    ad = settings.ACTIVE_DIR
    if not ad.connect_ad(creds['username'], creds['password']):
        return None
    return ad


# ---------------------------------------------------------------------------
# User Admin
# ---------------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Custom URLs
    # ------------------------------------------------------------------

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