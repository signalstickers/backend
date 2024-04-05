import datetime
import logging
import random
import re

from core.models import ApiKey, BotPreventionQuestion, ContributionRequest
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

logger = logging.getLogger(__name__)


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
