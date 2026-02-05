from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from .ad_conn import ADConnection
import logging

logget = logging.getLogger(__name__)

User = get_user_model()


class ActiveDirectoryBackend(BaseBackend):
    """
    Authenticate users against Active Directory
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
        
        ad = ADConnection()
        
        # check against AD
        if not ad.connect_ad(username, password):
            logger.warning(f"AD authentication failed for {username}")
            return None
        
        # AD success → get or create local user
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'is_active': True,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if not user.is_active:
            return None

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None