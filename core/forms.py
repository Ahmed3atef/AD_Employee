from django import forms
from employee import models as emp_models

class ADUserCreationForm(forms.Form):
    """
    Form to create a new user in Active Directory from the admin panel.
    The password is sent to AD only — it is NOT stored locally.
    """
    username = forms.CharField(
        max_length=100,
        help_text='sAMAccountName (e.g. user.name). Do NOT include @domain.',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. user.name',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'min 8 chars, mix of uppercase, lowercase, numbers',
        }),
        help_text='Password must meet AD complexity requirements.',
    )
    given_name = forms.CharField(
        max_length=100,
        label='First Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. User',
        }),
    )
    surname = forms.CharField(
        max_length=100,
        label='Last Name',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. Name',
        }),
    )
    email = forms.EmailField(
        required=False,
        help_text='Email address (optional). Auto-generated as username@domain if left blank.',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. user.name@eissa.local',
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
        help_text='(min 8 chars, mix of uppercase, lowercase, numbers).',
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
