from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
from django.conf import settings

class Job(models.Model):
    title = models.CharField(max_length=100)
    
    class Meta:
        indexes = [
            models.Index(fields=['title'], name='idx_job_title')
        ]
        ordering = ['title']
    def __str__(self):
        return self.title

class Department(models.Model):
    name = models.CharField(max_length=100)
    class Meta:
        indexes = [
            models.Index(fields=['name'], name='idx_department_name')
        ]
        ordering = ['name']
    def __str__(self):
        return self.name
    
    
class Employee(models.Model):
    # id = models.AutoField(primary_key=True)  # Django creates this automatically
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employee_profile'
    )
    
    full_name_en = models.CharField(max_length=255, null=True, blank=True)
    full_name_ar = models.CharField(max_length=255, null=True, blank=True)
    
    hire_date = models.DateField(default= timezone.now)
    
    nid = models.CharField(
        max_length=14,
        unique=True,
        db_index=True,
        verbose_name='National ID',
        validators=[
            RegexValidator(r'^[0-9]{14}$', 'National ID must be exactly 14 digits')
        ],
        null=True,
        blank=True,
        
    )
    
    job_title = models.ForeignKey(
        Job, 
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True,
        null=True,
        blank=True
    )
    
    department = models.ForeignKey(
        Department, 
        on_delete=models.PROTECT,
        related_name='employees',
        db_index=True,
        null=True,
        blank=True
    )
    
    
    class Meta:
        indexes = [
            models.Index(fields=['user'], name='idx_emp_user'),
            models.Index(fields=['nid'], name='idx_emp_nid'),
            models.Index(fields=['hire_date'], name='idx_emp_hire_date'),
            models.Index(fields=['full_name_en'], name='idx_emp_name_en'),
            models.Index(fields=['full_name_ar'], name='idx_emp_name_ar'),
            models.Index(fields=['department', 'job_title'], name='idx_emp_dept_job'),
        ]
        ordering = ['full_name_en']
    
    def __str__(self):
        job = self.job_title.title if self.job_title else "No Job Title"
        dept = self.department.name if self.department else "No Department"
        return f"{self.full_name_en or 'Unnamed'} - {job} - {dept}"