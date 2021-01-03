from datetime import timedelta
import uuid

from api.models.bot_prevention_questions import BotPreventionQuestion
from django.db import models
from django.utils import timezone


class ContributionRequestManager(models.Manager):
    def expired(self):
        """
        Return expired ContributionRequests (more than 2 hours old)
        """
        threshold = timezone.now() - timedelta(hours=2)
        return ContributionRequest.objects.filter(request_date__lt=threshold)


class ContributionRequest(models.Model):
    objects = ContributionRequestManager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client_ip = models.GenericIPAddressField(protocol="IPv4")
    question = models.ForeignKey(BotPreventionQuestion, on_delete=models.CASCADE)
    request_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "contributionrequests"

    def __str__(self):
        return str(self.id)
