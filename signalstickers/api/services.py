import datetime
import random
import re

from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

from api.models import BotPreventionQuestion, ContributionRequest


def new_contribution_request(client_ip):
    cont_req = ContributionRequest(
        client_ip=client_ip, question=random.choice(BotPreventionQuestion.objects.all())
    )
    cont_req.save()
    return cont_req


def check_contribution_request(contribution_id, client_answer, client_ip):
    try:
        cont_req = ContributionRequest.objects.get(
            id=contribution_id, client_ip=client_ip
        )
    except ObjectDoesNotExist:
        return False, "Invalid contribution request. Try again."

    if cont_req.request_date + datetime.timedelta(hours=1) < now():
        return False, "Expired contribution request. Try again."

    correct_answer = re.sub(r"[^a-z]", "", cont_req.question.answer.strip().lower())
    client_answer = re.sub(r"[^a-z]", "", client_answer.strip().lower())

    if correct_answer == client_answer:
        cont_req.delete()
        return True, None

    return False, "Wrong answer."
