import datetime
import logging
import random
import re

from core.models import ApiKey, BotPreventionQuestion, ContributionRequest
from core.notifications import NotificationPriority, notify
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.utils.timezone import now
import requests

logger = logging.getLogger("main")


def clear_contribution_requests():
    """
    Delete expired ContributionRequests (more than 2 hours old), and return the
    number of CR deleted.
    """
    nb_deleted, _ = ContributionRequest.objects.expired().delete()
    return nb_deleted


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


def notify_pack_escalated(pack, username):
    """
    Send a HIGH-priority ntfy notification when a pack is escalated.
    """
    logger.info("Pack %s (%s) escalated", pack.title, pack.pack_id)
    notify(
        "signalstickers-admin",
        "Escalated pack",
        f"Pack '{pack.title}' escalated by {username}, please review",
        priority=NotificationPriority.HIGH,
        tags=["arrow_heading_up"],
        click_url=f"https://{settings.ALLOWED_HOSTS[0]}/{settings.ADMIN_URL}",
    )


def notify_admin_login(username, client_ip):
    """
    Send a ntfy notification when an admin user logs into the admin panel.
    """
    logger.info("Admin login: %s from %s", username, client_ip)
    notify(
        "signalstickers-admin",
        "Admin login",
        f"Admin '{username}' logged in from {client_ip}",
        priority=NotificationPriority.DEFAULT,
        tags=["lock"],
        click_url=f"https://{settings.ALLOWED_HOSTS[0]}/{settings.ADMIN_URL}",
    )


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
        return False, "Security verification failed, reload and try again"

    if cont_req.request_date + datetime.timedelta(hours=1) < now():
        cont_req.delete()
        logger.info("Received an expired ContributionRequest")
        return (
            False,
            "Security verification failed, reload and try again."
            " Reason: you took too long",
        )

    correct_answer = re.sub(r"[^a-z0-9]", "", cont_req.question.answer.strip().lower())
    client_answer = re.sub(r"[^a-z0-9]", "", client_answer.strip().lower())

    if correct_answer == client_answer:
        cont_req.delete()
        return True, None

    return False, "Wrong answer"


def check_api_key(key):
    try:
        key_obj = ApiKey.objects.get(key=key)
        return key_obj
    except:  # pylint: disable=bare-except
        return False
