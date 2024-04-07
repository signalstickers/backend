from ninja import Schema
from pydantic import StringConstraints, model_validator
from typing_extensions import Annotated

# ---------- Common ---------- #

PackIDType = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=32,
        max_length=32,
        pattern=r"^[a-f0-9]{32}$",
    ),
]


PackKeyType = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=64,
        max_length=64,
        pattern=r"^[a-f0-9]{64}$",
    ),
]


class _PackMetaIdentifiers(Schema):
    id: PackIDType
    key: PackKeyType


class _PackMeta(_PackMetaIdentifiers):
    source: str = ""
    tags: list[str] = []
    nsfw: bool = False
    original: bool = False


# ---------- Requests ---------- #


class PackMetaRequest(_PackMeta):
    """
    Requires full pack metadata
    """


class PackIdentifierRequest(_PackMetaIdentifiers):
    """
    Requires a pack ID and key
    """


# ---------- Responses ---------- #


class PackMetaResponse(_PackMeta):
    animated: bool = False
    editorschoice: bool = False
    totalviews: int = 0
    hotviews: int = 0


class PackManifestResponse(Schema):
    title: str
    author: str
    cover_id: int = 0


class PackResponse(Schema):
    meta: PackMetaResponse
    manifest: PackManifestResponse

    @model_validator(mode="before")
    @classmethod
    def shape_from_queryset(cls, data):

        tags = [tag.name for tag in data.tags]

        # Furry packs should only contain a "furry" tag
        if "furry" in tags:
            tags = ["furry"]

        return {
            "meta": {
                "id": data.pack_id,
                "key": data.pack_key,
                "source": data.source,
                "tags": tags,
                "nsfw": data.nsfw,
                "original": data.original,
                "animated": data.animated,
                "editorschoice": data.editorschoice,
                "totalviews": data.total_views,
                "hotviews": data.hot_views,
            },
            "manifest": {
                "title": data.title,
                "author": data.author,
                "cover_id": data.id_cover,
            },
        }
