from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager that doesn't require email"""
    
    def create_user(self, username, password=None, **extra_fields):
        """Create and return a regular user"""
        if not username:
            raise ValueError('The Username field must be set')
        
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        extra_fields.setdefault('is_active', True)
        
        user = self.model(username=username, **extra_fields)
        
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, password=None, **extra_fields):
        """Create and return a superuser"""
        if not password:
            raise ValueError('Superuser must have a password')
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, password, **extra_fields)


class User(AbstractUser):
    
    # Remove inherited fields
    first_name = None
    last_name = None
    email = None
    
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
    
    objects = UserManager()
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []
    
    def __str__(self):
        return self.username
    
    class Meta:
        indexes = [
            models.Index(fields=['username'], name='idx_user_username'),
        ]
        ordering = ['username']