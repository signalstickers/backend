from time import sleep

from apps.stickers.models import Pack, PackStatus
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from yaml import Dumper, Loader, dump, load


class Command(BaseCommand):
    help = "Import stickers from YAML in the DB."

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=open)

    def handle(self, *args, **options):

        nb_imported = 0
        data = load(options["input_file"], Loader=Loader)

        for pack_id, pack_data in dict(reversed(list(data.items()))).items():

            try:
                pack = Pack.objects.new(
                    pack_id=pack_id,
                    pack_key=pack_data["key"],
                    source=pack_data.get("source", ""),
                    status=PackStatus.ONLINE.name,
                    nsfw=pack_data.get("nsfw", False),
                    original=pack_data.get("original", False),
                    tags=pack_data.get("tags", None),
                    tweeted=True,
                    editorschoice=data.get("editorschoice", False),
                )

                nb_imported += 1
                self.stdout.write(f"\rImported: {nb_imported} ", ending="")

                if pack.animated_detected != pack_data.get(
                    "animated", False
                ):  # pragma: no cover
                    self.stdout.write(
                        f"Animated detection failed for pack {pack_id} (detected: {pack.animated_detected}, YML: {pack_data.get('animated', False)}). Using detection value."
                    )

            except IntegrityError:
                self.stdout.write(f"Pack {pack_id} not imported (duplicate)")

            except ValidationError as e:
                self.stdout.write(
                    f"Pack {pack_id} not imported (key: {pack_data['key']}): {e}"
                )

        self.stdout.write(f"\nAll done! Imported: {nb_imported}")
