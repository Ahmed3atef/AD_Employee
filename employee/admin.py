from django.contrib import admin
from . import models

admin.site.register(models.Job)
admin.site.register(models.Department)

@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user__username', 'full_name_en', 'full_name_ar', 'hire_date', 'nid', 'job_title', 'department')
    list_filter = ('job_title', 'department')
    search_fields = ('user__username', 'full_name_en', 'full_name_ar')
    ordering = ('full_name_en',)
    
