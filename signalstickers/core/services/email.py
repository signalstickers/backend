import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage

logger = logging.getLogger("main")


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
