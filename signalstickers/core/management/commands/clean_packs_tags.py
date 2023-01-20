from core.models.pack import Pack
from core.models.pack_status import PackStatus
from core.models.tag import Tag
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Look for wrong or malformed tags in packs and correct them."

    def handle(self, *args, **options):
        # Get all packs except REFUSED ones
        packs = (
            Pack.objects.exclude(status=PackStatus.REFUSED.name)
            .prefetch_related("tags")
            .order_by("-id")
        )

        for pack in packs:
            pack_tags = pack.tags.all()

            for tag in pack_tags:
                # Malformed tag as "#pastel #unicorn #flowers" should be 3 separated tags
                if "#" in tag.name:
                    new_names = tag.name.split("#")
                    for new_name in new_names:
                        if new_name:
                            new_tag, _ = Tag.objects.get_or_create(
                                name=new_name.strip()
                            )
                            pack.tags.add(new_tag)
                    tag.delete()
