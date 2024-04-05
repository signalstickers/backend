import datetime
import logging
import random
import re

from core.models import ApiKey, BotPreventionQuestion, ContributionRequest, Pack
from django.conf import settings
from django.contrib.admin.models import LogEntry
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.utils.timezone import now
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

        resp = requests.post(url, json=data, headers=headers, timeout=45)

        if resp.status_code not in range(200, 300):
            raise Exception(resp.text)  # pylint: disable=broad-exception-raised

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


def send_email_pack_escalated():
    """
    Send an email to the users in group `email_notification_on_escalated`)
    """

    # Recipients
    user_model = get_user_model()
    recipients = user_model.objects.filter(
        groups__name="email_notification_on_escalated"
    ).values_list("email", flat=True)

    # Packs
    escalated_packs = (
        Pack.objects.escalated().order_by("id").values_list("id", flat=True)
    )
    packs_changed_yesterday = (
        LogEntry.objects.filter(
            action_time__date=datetime.datetime.today() - datetime.timedelta(days=1)
        )
        .filter(content_type__model="pack")
        .order_by("object_id")
        .distinct("object_id")
        .values_list("object_id", flat=True)
    )

    nb_packs_escalated_yesterday = len(
        [
            pack_id
            for pack_id in escalated_packs
            if str(pack_id) in packs_changed_yesterday
        ]
    )

    if not nb_packs_escalated_yesterday:
        logger.info("No pack escalated yesterday")
        return

    logger.info("%i pack escalated yesterday", nb_packs_escalated_yesterday)
    message = f"""\
Hello! 👋

{nb_packs_escalated_yesterday} have been escalated today. Please review!

"""
    email = EmailMessage(
        f"{nb_packs_escalated_yesterday} escalated packs",
        message,
        settings.EMAIL_FROM,
        [],  # to
        list(recipients),  # bcc
    )
    try:
        email.send()
    except Exception as ex:  # pylint: disable=broad-except
        logger.error("Error sending e-mail: %s", ex)


def new_contribution_request(client_ip):
    cont_req = ContributionRequest(
        client_ip=client_ip,
        question=random.choice(BotPreventionQuestion.objects.all()),  # nosec
    )
    cont_req.save()
    return cont_req


def check_contribution_request(contribution_id, client_answer, client_ip):
    try:
        cont_req = ContributionRequest.objects.get(
            id=contribution_id, client_ip=client_ip
        )
    except ObjectDoesNotExist:
        logger.info("Received an invalid ContributionRequest")
        return False, "Invalid contribution request. Try again."

    if cont_req.request_date + datetime.timedelta(hours=1) < now():
        cont_req.delete()
        logger.info("Received an expired ContributionRequest")
        return False, "Expired contribution request. Try again."

    correct_answer = re.sub(r"[^a-z0-9]", "", cont_req.question.answer.strip().lower())
    client_answer = re.sub(r"[^a-z0-9]", "", client_answer.strip().lower())

    if correct_answer == client_answer:
        cont_req.delete()
        return True, None

    return False, "Wrong answer."


def check_api_key(key):
    try:
        key_obj = ApiKey.objects.get(key=key)
        return key_obj
    except:  # pylint: disable=bare-except
        return False
