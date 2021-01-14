import logging

from apps.core.services import clear_contribution_requests
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Clear expired ContributionRequests"

    def handle(self, *args, **options):
        nb = clear_contribution_requests()
        print(nb)
