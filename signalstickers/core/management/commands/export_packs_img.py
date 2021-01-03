import re
import sys

from core.models import Pack
from core.utils import get_pack_from_signal
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Export stickers img to files."

    def handle(self, *args, **options):
        nb_exported = 0

        for pack in Pack.objects.all():
            pack_data = get_pack_from_signal(pack.pack_id, pack.pack_key)

            for sticker in pack_data.stickers:

                img = sticker.image_data
                sticker_id = int(sticker.id)
                if b"\x61\x63\x54\x4C" in img:  # APNG acTL chunk
                    ext = "png"
                elif img.startswith(b"\x89\x50\x4E\x47\x0D\x0A\x1A\x0A"):  # PNG
                    ext = "png"
                elif img.startswith(b"\x47\x49\x46\x38\x39\x61"):
                    ext = "gif"
                elif (
                    img.startswith(b"\x52\x49\x46\x46")
                    and img[8:12] == b"\x57\x45\x42\x50"
                ):
                    ext = "webp"
                else:
                    print("Unknown file type")

                nb_exported += 1

                if not re.match(r"^[a-z0-9]{32}$", pack.pack_id):
                    # Should never happend but hey
                    print("Forbidden char in pack id ")
                    sys.exit()

                filename = f"/tmp/export_sst/{pack.pack_id}_{sticker_id}.{ext}"  # nosec

                with open(filename, "bw") as f_out:
                    f_out.write(img)

        self.stdout.write(f"\nAll done! Exported: {nb_exported} files.")
