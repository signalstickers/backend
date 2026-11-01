from api_v2.schemas.pack import PackIDType, PackKeyType
from core.models import AIReviewStatus
from ninja import Schema
from pydantic import Field, field_validator, model_validator
from typing_extensions import Annotated


class InReviewPackResponse(Schema):
    id: PackIDType
    key: PackKeyType
    source: str = ""
    submitter_comments: str = ""
    tags: list[str] = []

    @model_validator(mode="before")
    @classmethod
    def shape_from_pack(cls, data):
        return {
            "id": data.pack_id,
            "key": data.pack_key,
            "source": data.source,
            "submitter_comments": data.submitter_comments,
            # data.tags is already a list of tags (DjangoGetter materializes it)
            "tags": [tag.name for tag in data.tags],
        }


class AIReviewRequest(Schema):
    pack_id: PackIDType
    status: AIReviewStatus
    confidence: Annotated[float, Field(ge=0.0, le=1.0)]
    review_comment: str = ""
    nsfw: bool = False
    tags_match: bool = False
    alert: bool = False

    @field_validator("status", mode="before")
    @classmethod
    def _status_from_name(cls, value):
        """
        The AI bot sends the enum member _name_ ("ACCEPT"/"REFUSE"),
        as in API v1. Anything else falls through to pydantic's
        standard enum validation (422).
        """
        if isinstance(value, str):
            try:
                return AIReviewStatus[value]
            except KeyError:
                pass
        return value
