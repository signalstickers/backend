import logging
import time

import boto3
from django.conf import settings
from libs.twitter_bot import tweet_pack

from apps.api.models import ContributionRequest
from apps.stickers.models import Pack

logger = logging.getLogger("main")


def clear_contribution_requests():
    """
    Delete expired ContributionRequests (more than 2 hours old), and return the
    number of CR deleted.
    """
    nb_deleted, _ = ContributionRequest.objects.expired().delete()
    return nb_deleted


def tweet_command():
    """
    Tweet packs tagged as 'not tweeted'
    """

    not_tweeted_packs = Pack.objects.not_twitteds()

    nb_packs_twitted = 0
    errs = []

    for pack in not_tweeted_packs:
        try:
            logger.info("Start tweeting about %s", pack.pack_id)
            tweet_pack(pack)
            logger.info("Tweet about %s done", pack.pack_id)

            # Set pack as "tweeted"
            pack.tweeted = True
            pack.save()
            nb_packs_twitted += 1

        except Exception as e:
            mess = f"Error while tweeting {pack.pack_id}: {e}"
            logger.error(mess)
            errs.append(mess)

    return nb_packs_twitted, errs


def invalidate_cdn():
    """
    Send an invalidation request to the CDN
    """

    try:
        cloudfront_client = boto3.client(
            "cloudfront",
            aws_access_key_id=settings.CLOUDFRONT_CONF["access_key"],
            aws_secret_access_key=settings.CLOUDFRONT_CONF["secret_key"],
        )

        resp = cloudfront_client.create_invalidation(
            DistributionId=settings.CLOUDFRONT_CONF["distribution_id"],
            InvalidationBatch={
                "Paths": {
                    "Quantity": len(settings.CLOUDFRONT_CONF["invalidation_path"]),
                    "Items": settings.CLOUDFRONT_CONF["invalidation_path"],
                },
                "CallerReference": f"{int(time.time())}",
            },
        )
    except Exception as e:
        mess = f"Error when invalidating caches: {e}"
        logger.error(mess)
        return False, mess

    return True, resp
