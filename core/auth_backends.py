from django.contrib.auth.backends import BaseBackend 
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404 
from django.conf import settings 
import logging 


logger = logging.getLogger(__name__) 
User = get_user_model() 



class ActiveDirectoryBackend(BaseBackend): 
    """ Authenticate users against Active Directory """ 
    def sync_users(self): 
        ad = settings.ACTIVE_DIR 
        ad.connect_ad() 
        ad.get_all_users_full_info() 
    def authenticate(self, request, username=None, password=None, **kwargs): 
        if not username or not password: 
            return None 
        ad = settings.ACTIVE_DIR 
        # check against AD 
        if not ad.connect_ad(username, password): 
            logger.warning(f"AD authentication failed for {username}") 
            return None 
        # Capture credentials in session for later use in Sync/Transfer actions 
        if request: 
            request.session.flush()            
            request.session.set_expiry(3600)
            request.session['ad_user'] = username 
            request.session['ad_password'] = password 
        # AD success → get or create local user 
        user = get_object_or_404(User, username=username)
        if not user or not user.is_active: 
            return None 
        return user 
    def get_user(self, user_id): 
        try: 
            return User.objects.get(pk=user_id) 
        except User.DoesNotExist: 
            return None