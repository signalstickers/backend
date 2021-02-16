import logging

from apps.core.services import invalidate_cdn
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Clean Cloudflare caches"

    def handle(self, *args, **options):
        invalidate_cdn()

