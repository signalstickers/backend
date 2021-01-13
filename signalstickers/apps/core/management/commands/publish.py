import logging

from apps.core.services import publish_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Serialize all packs and publish them on Github"

    def handle(self, *args, **options):
        publish_command()

