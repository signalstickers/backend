import logging
from time import sleep

from apps.stickers.models import Pack
from django.core.management.base import BaseCommand
from libs.twitter_bot import tweet_pack

logger = logging.getLogger("main")


class Command(BaseCommand):
    help = "Tweet packs tagged as 'not tweeted'"

    def handle(self, *args, **options):
        not_tweeted_packs = Pack.objects.not_twitteds()

        for pack in not_tweeted_packs:
            try:
                logger.info("Start tweeting about %s", pack.pack_id)
                tweet_pack(pack)
                logger.info("Tweet about %s done", pack.pack_id)

                # Set pack as "tweeted"
                pack.tweeted = True
                pack.save()

            except Exception as e:
                logger.error("Error while tweeting %s: %s", pack.pack_id, e)

            sleep(3)
