import logging

from core.services import tweet_command
from django.core.management.base import BaseCommand

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Tweet packs tagged as 'not tweeted'"

    def handle(self, *args, **options):
        tweet_command()
