import uuid

from django.db import models

from .bot_prevention_questions import BotPreventionQuestion


class ContributionRequest(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_ip = models.GenericIPAddressField(protocol="IPv4")
    question = models.ForeignKey(BotPreventionQuestion, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contributionrequests"

    def __str__(self):
        return str(self.id)
