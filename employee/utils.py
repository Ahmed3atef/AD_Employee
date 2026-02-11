from django.core.cache import cache
from django.conf import settings
import re

def get_clean_ldap_val(entry, attr_name):
    """Extract a clean string value from an LDAP entry attribute."""
    val = getattr(entry, attr_name, None)
    if not val or val == [] or str(val).strip() == "":
        return None
    if isinstance(val, list):
        return str(val[0]).strip()
    return str(val).strip()


def extract_ou_from_dn(dn):
    """Return the first OU component from a Distinguished Name, or None."""
    match = re.search(r'OU=([^,]+)', dn or "")
    return match.group(1).strip() if match else None


def get_ad_connection(request):
    """
    Retrieve cached AD credentials and return an authenticated AD connection.
    Returns (ad_connection, error_message).  On success error_message is None.
    """
    creds = cache.get(f'ad_creds_{request.user.id}')
    if not creds or not creds.get('username') or not creds.get('password'):
        return None, "Credentials not found in cache. Please re-login."

    ad = settings.ACTIVE_DIR
    if not ad.connect_ad(creds['username'], creds['password']):
        return None, "Failed to connect to AD with your credentials."

    return ad, None

def get_client_ip(request):
    """Get the client IP address from the request."""
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')
