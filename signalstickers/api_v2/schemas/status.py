from typing import Optional

from api_v2.schemas.pack import PackIDType
from core.models import PackStatus
from ninja import Schema
from pydantic import PlainSerializer
from typing_extensions import Annotated

# ---------- Common ---------- #


# ---------- Requests ---------- #


# ---------- Responses ---------- #


class StatusResponse(Schema):
    pack_title: str
    pack_id: PackIDType
    status: Annotated[
        PackStatus,
        PlainSerializer(
            lambda x: x.name,
            return_type=str,
        ),
    ]
    status_comments: Optional[str] = None
