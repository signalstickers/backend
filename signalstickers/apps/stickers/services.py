import os
from typing import List

import anyio
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404

from apps.stickers.models import Pack, PackStatus, Tag


def new_pack(
    pack_id,
    pack_key,
    status,
    source="",
    nsfw=False,
    original=False,
    submitter_comments="",
    tags=None,
    api_via="",
    tweeted=False,
) -> Pack:

    if api_via:
        source = source.strip() + f" (via {api_via})"
    else:
        source = source.strip()

    tags = tags or []
    if len(tags) > 40:
        raise ValidationError("Too many tags (max 40).")
    pack = Pack(
        pack_id=pack_id.strip(),
        pack_key=pack_key.strip(),
        source=source,
        status=status,
        nsfw=nsfw,
        original=original,
        submitter_comments=submitter_comments,
        tweeted=tweeted,
    )

    pack.clean()

    with transaction.atomic():
        pack.save()

        tags_obj_list = []
        for tag in tags:
            tag_obj, _ = Tag.objects.get_or_create(name=tag.lower())
            tags_obj_list.append(tag_obj)

        if tags_obj_list:
            pack.tags.add(*tags_obj_list)

    return pack
