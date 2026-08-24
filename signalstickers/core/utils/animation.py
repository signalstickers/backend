from django.core.exceptions import ValidationError


def detect_animated_pack(lib_pack):
    """
    Take a pack from signalstickers_client and return a boolean describing if
    the pack is animated or not. A pack will be animated if at least one of its
    stickers is a APNG or a GIF.
    Will raise a `ValidationError` if the pack format is invalid.
    """

    for sticker in lib_pack.stickers:
        if b"\x61\x63\x54\x4c" in sticker.image_data:  # APNG acTL chunk
            return True
        if sticker.image_data.startswith(
            b"\x47\x49\x46\x38\x39\x61"
        ):  # GIF89a magic numbers
            return True
        if (
            b"\x41\x4e\x49\x4d" in sticker.image_data  # ANIM chunck
            and b"\x57\x45\x42\x50" in sticker.image_data  # WEBP
        ):
            # Animated WebP: invalid.
            raise ValidationError(
                "Animated WebP are invalid; this pack can not be added."
            )
    return False
