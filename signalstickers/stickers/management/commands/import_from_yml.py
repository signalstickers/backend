from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from stickers.models import PackStatus
from stickers.services import new_pack
from yaml import Dumper, Loader, dump, load


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def add_arguments(self, parser):
        parser.add_argument("input_file", type=open)

    def handle(self, *args, **options):

        nb_imported = 0
        data = load(options["input_file"], Loader=Loader)

        for pack_id, pack_data in data.items():

            try:
                pack = new_pack(
                    pack_id=pack_id,
                    pack_key=pack_data["key"],
                    source=pack_data.get("source", ""),
                    status=PackStatus.ONLINE.name,
                    nsfw=pack_data.get("nsfw", False),
                    original=pack_data.get("original", False),
                    animated=pack_data.get("animated", False),
                    tags=pack_data.get("tags", None),
                )
                nb_imported += 1
                print("Imported: ", nb_imported, end="\r", flush=True)

                if pack.animated_detected != pack_data.get("animated", False):
                    print(
                        f"Animated detection failed for pack {pack_id} (detected: {pack.animated_detected}, YML: {pack_data.get('animated', False)}). Using detection value."
                    )

            except IntegrityError:
                print(f"Pack {pack_id} not imported (duplicate)")

            except ValidationError:
                print(
                    f"Pack {pack_id} not imported (invalid) (key: {pack_data['key']})"
                )

        print("\nAll done! Imported:", nb_imported)
