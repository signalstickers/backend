from core.models import ApiKey
from django.core.exceptions import ValidationError


def check_api_key(key):
    try:
        return ApiKey.objects.get(key=key)
    except (ApiKey.DoesNotExist, ValidationError):
        return False
