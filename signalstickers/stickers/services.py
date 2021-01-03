import os

import anyio

from stickers.models import Pack, Tag
from stickers.utils import get_pack_from_signal


def new_pack(
    pack_id,
    pack_key,
    status,
    source="",
    nsfw=False,
    original=False,
    animated=False,
    submitter_comments="",
    tags=None,
) -> Pack:

    pack = Pack(
        pack_id=pack_id.strip(),
        pack_key=pack_key.strip(),
        source=source.strip(),
        status=status,
        nsfw=nsfw,
        original=original,
        animated=animated,
        submitter_comments=submitter_comments,
    )

    pack.clean()
    pack.save()

    tags_obj_list = []
    for tag in tags:
        tag_obj, _ = Tag.objects.get_or_create(name=tag.lower())
        tags_obj_list.append(tag_obj)

    if tags_obj_list:
        pack.tags.add(*tags_obj_list)

    return pack
