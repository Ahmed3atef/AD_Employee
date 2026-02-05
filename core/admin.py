from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Fields to display in the user list
    list_display = ('username', 'is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('username',)
    ordering = ('username',)
    
    # Fields when viewing/editing a user
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'is_active', 'is_staff'),
        }),
    )
    
    # Remove first_name, last_name, email from all fieldsets
    filter_horizontal = ('groups', 'user_permissions')