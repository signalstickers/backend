import anyio
from signalstickers_client import StickersClient


def get_pack_from_signal(pack_id, pack_key):
    async def _get_pack(pack_id, pack_key):
        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)
        return pack

    try:
        return anyio.run(_get_pack, pack_id, pack_key)
    except:
        return None


def detect_animated_pack(lib_pack):
    """
    Takes a pack from signalstickers_client and return a boolean describing if
    the pack is animated or not. A pack will be animated if at least one of its
    stickers is a APNG or a GIF.
    """

    for sticker in lib_pack.stickers:
        if b"\x61\x63\x54\x4C" in sticker.image_data:  # APNG acTL chunk
            return True
        if sticker.image_data.startswith(
            b"\x47\x49\x46\x38\x39\x61"
        ):  # GIF89a magic numbers
            return True
    return False
