import logging

from core.services import send_email_pack_escalated
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Check yesterday's escalated packs, and notify admins."

    def handle(self, *args, **options):
        send_email_pack_escalated()
