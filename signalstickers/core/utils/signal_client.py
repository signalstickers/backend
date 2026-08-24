import anyio
from signalstickers_client import StickersClient


def get_pack_from_signal(pack_id, pack_key):  # pragma: no cover
    """
    Simple async -> sync wrapper around StickersClient.
    """

    async def _get_pack(pack_id, pack_key):
        async with StickersClient() as client:
            pack = await client.get_pack(pack_id, pack_key)
        return pack

    try:
        return anyio.run(_get_pack, pack_id, pack_key)
    except:  # pylint: disable=bare-except
        return None
