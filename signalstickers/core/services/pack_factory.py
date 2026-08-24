from core.models.pack import Pack
from core.models.tag import Tag
from django.core.exceptions import ValidationError
from django.db import transaction


def create_pack(
    pack_id,
    pack_key,
    status,
    source="",
    nsfw=False,
    original=False,
    submitter_comments="",
    tags=None,
    api_via="",
    editorschoice=False,
):
    """
    Create a new pack with validation, save it, and return it. Use this
    function instead of create(), as this one also create related tags
    properly. Return the pack which has been created.
    """
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
        editorschoice=editorschoice,
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
