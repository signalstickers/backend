import logging

from api.models import ContributionRequest
from core.models import Pack
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from libs.twitter_bot import tweet_pack
import requests

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

        except Exception as e:  # pylint: disable=broad-except
            mess = f"Error while tweeting {pack.pack_id}: {e}"
            logger.error(mess)
            errs.append(mess)

    return nb_packs_twitted, errs


def invalidate_cdn():
    """
    Send an invalidation request to the CDN
    """

    try:

        url = f'https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_CONF["zone_id"]}/purge_cache'
        headers = {"Authorization": f'Bearer {settings.CLOUDFLARE_CONF["token"]}'}
        data = {"purge_everything": True}

        resp = requests.post(url, json=data, headers=headers)

        if resp.status_code not in range(200, 300):
            raise Exception(resp.text)

    except Exception as e:  # pylint: disable=broad-except
        mess = f"Error when invalidating caches: {e}"
        logger.error(mess)
        return False, str(e)

    return True, resp.text


def send_email_on_pack_propose(pack):
    """
    Send an email to the reviewers (== users in group `email_notification_on_propose`)
    """
    user_model = get_user_model()
    recipients = user_model.objects.filter(
        groups__name="email_notification_on_propose"
    ).values_list("email", flat=True)
    message = f"""\
Hello! 👋

A new pack was proposed!

{pack.title}, by {pack.author}

Comment:
{pack.submitter_comments or "N/A"}
"""
    email = EmailMessage(
        f"Propose: {pack.title}",
        message,
        settings.EMAIL_FROM,
        [],  # to
        list(recipients),  # bcc
    )
    try:
        email.send()
    except Exception as ex:  # pylint: disable=broad-except
        logger.error("Error sending e-mail: %s", ex)
