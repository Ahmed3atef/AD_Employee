from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone

class Job(models.Model):
    title = models.CharField(max_length=100)
    
    class Meta:
        db_table = 'job'
        indexes = [
            models.Index(fields=['title'], name='idx_job_title')
        ]
    def __str__(self):
        return self.title

class Department(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        db_table = 'department'
        indexes = [
            models.Index(fields=['name'], name='idx_department_name')
        ]
    def __str__(self):
        return self.name
    
    
class Employee(models.Model):
    username = models.CharField(
        max_length=255, 
        unique=True,
        db_index=True,
        help_text='AD sAMAccountName or userPrincipalName',
        validators=[
            RegexValidator(
                r'^[a-zA-Z0-9._-]+(@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})?$',
                'Username must be in sAMAccountName format (e.g., jsmith) or UPN format (e.g., jsmith@domain.com)'
            )
        ]
    )
    
    full_name_en = models.CharField(max_length=255)
    full_name_ar = models.CharField(max_length=255)
    
    hire_date = models.DateField(default= timezone.now)
    
    nid = models.CharField(
        max_length=14,
        unique=True,
        db_index=True,
        verbose_name='National ID',
        validators=[
            RegexValidator(r'^[0-9]{14}$', 'National ID must be exactly 14 digits')
        ]
    )
    
    job_title = models.ForeignKey(
        Job, 
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True
    )
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True
    )
    
    
    class Meta:
        db_table = 'employee'
        indexes = [
            models.Index(fields=['username'], name='idx_emp_username'),
            models.Index(fields=['nid'], name='idx_emp_nid'),
            models.Index(fields=['hire_date'], name='idx_emp_hire_date'),
            models.Index(fields=['full_name_en'], name='idx_emp_name_en'),
            models.Index(fields=['full_name_ar'], name='idx_emp_name_ar'),
            models.Index(fields=['department', 'job_title'], name='idx_emp_dept_job'),
        ]
        ordering = ['full_name_en']
    
    def __str__(self):
        return f"{self.full_name_en} - {self.job_title.title} - {self.department.name}"