import os
from typing import List

import anyio
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from stickers.models import Pack, PackStatus, Tag
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

    tags = tags or []
    if len(tags) > 40:
        raise ValidationError("Too many tags (max 40).")

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


def get_all_online_packs() -> List[PackStatus]:
    return Pack.objects.filter(status=PackStatus.ONLINE.name).order_by("-id")


def get_pack(pack_id) -> Pack:
    return get_object_or_404(Pack, pack_id=pack_id)
