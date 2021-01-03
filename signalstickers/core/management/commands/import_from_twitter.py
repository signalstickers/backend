from core.models import Pack, PackStatus
from django.core.management.base import BaseCommand
from libs.twitter_bot.query_twitter_packs import query_twitter


class Command(BaseCommand):
    help = "Import latest sticker packs from Twitter."

    def handle(self, *args, **options):

        for pack in query_twitter():

            try:
                Pack.objects.new(
                    pack_id=pack[0],
                    pack_key=pack[1],
                    source=pack[2],
                    status=PackStatus.IN_REVIEW.name,
                    original=True,
                    submitter_comments="Automatically imported from Twitter",
                )
            except:  # pylint:disable=bare-except
                pass
