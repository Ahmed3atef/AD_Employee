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


class OUTransferLog(models.Model):
    """
    Audit log for tracking OU transfer operations
    This will appear in Django Admin's Recent Actions
    """
    
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success'),
    ]
    
    # Who performed the action
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ou_transfers_performed',
        verbose_name='Performed By',
        help_text='Admin user who performed the transfer'
    )
    
    # Employee being transferred
    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ou_transfer_logs',
        verbose_name='Employee',
        help_text='Employee record (if exists in database)'
    )
    
    employee_username = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name='Username',
        help_text='sAMAccountName of the transferred user'
    )
    
    employee_display_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name='Display Name',
        help_text='Display name at time of transfer'
    )
    
    # Transfer details
    old_ou = models.CharField(
        max_length=255,
        verbose_name='From OU',
        help_text='Source Organizational Unit'
    )
    
    new_ou = models.CharField(
        max_length=255,
        verbose_name='To OU',
        help_text='Destination Organizational Unit'
    )
    
    old_dn = models.TextField(
        verbose_name='Old DN',
        help_text='Full Distinguished Name before transfer'
    )
    
    new_dn = models.TextField(
        null=True,
        blank=True,
        verbose_name='New DN',
        help_text='Full Distinguished Name after transfer'
    )
    
    # Database sync
    database_updated = models.BooleanField(
        default=False,
        verbose_name='DB Updated',
        help_text='Whether database department was updated'
    )
    
    old_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_from',
        verbose_name='Old Department',
        help_text='Previous department in database'
    )
    
    new_department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transfers_to',
        verbose_name='New Department',
        help_text='New department in database'
    )
    
    # Status and metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success',
        db_index=True,
        verbose_name='Status'
    )
    
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='Error Message',
        help_text='Error details if transfer failed'
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='IP Address',
        help_text='IP address of the admin who performed the action'
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        verbose_name='Timestamp'
    )
    
    notes = models.TextField(
        null=True,
        blank=True,
        verbose_name='Notes',
        help_text='Additional notes or comments'
    )
    
    class Meta:
        verbose_name = 'OU Transfer Log'
        verbose_name_plural = 'OU Transfer Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp'], name='idx_transfer_timestamp'),
            models.Index(fields=['employee_username'], name='idx_transfer_username'),
            models.Index(fields=['status'], name='idx_transfer_status'),
            models.Index(fields=['performed_by', '-timestamp'], name='idx_transfer_user_time'),
        ]
        permissions = [
            ('view_transfer_audit', 'Can view transfer audit logs'),
            ('export_transfer_audit', 'Can export transfer audit logs'),
        ]
    
    def __str__(self):
        return f"{self.employee_username}: {self.old_ou} → {self.new_ou} ({self.get_status_display()})"
    
    def get_short_description(self):
        """Used for admin Recent Actions"""
        return f"Transferred {self.employee_display_name or self.employee_username} from {self.old_ou} to {self.new_ou}"