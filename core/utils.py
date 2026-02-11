from django.core.cache import cache
from django.conf import settings

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

