from core.models import ApiKey


def check_api_key(key):
    try:
        key_obj = ApiKey.objects.get(key=key)
        return key_obj
    except:  # pylint: disable=bare-except
        return False
