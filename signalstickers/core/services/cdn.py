import logging

from django.conf import settings
import requests

logger = logging.getLogger("main")


def invalidate_cdn():
    """
    Send an invalidation request to the CDN
    """

    try:

        url = f'https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_CONF["zone_id"]}/purge_cache'
        headers = {"Authorization": f'Bearer {settings.CLOUDFLARE_CONF["token"]}'}
        data = {"purge_everything": True}

        resp = requests.post(url, json=data, headers=headers, timeout=45)

        if resp.status_code not in range(200, 300):
            raise Exception(resp.text)  # pylint: disable=broad-exception-raised

    except Exception as e:  # pylint: disable=broad-except
        mess = f"Error when invalidating caches: {e}"
        logger.error(mess)
        return False, str(e)

    return True, resp.text
