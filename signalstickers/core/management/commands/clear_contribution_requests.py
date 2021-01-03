import logging

from core.services import clear_contribution_requests
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Clear expired ContributionRequests"

    def handle(self, *_, **__):
        nb_cleared = clear_contribution_requests()
        if nb_cleared:
            logger.info("Cleared %i ContributionRequests", nb_cleared)
