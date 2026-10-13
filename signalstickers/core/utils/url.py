from urllib.parse import urlparse

from django.conf import settings


def is_url(str_in):
    try:
        result = urlparse(str_in)
        return all([result.scheme, result.netloc])
    except:  # pylint: disable=bare-except
        return False


def admin_url():
    return f"https://{settings.ALLOWED_HOSTS[0]}/{settings.ADMIN_URL}"
