from typing import Literal

from api_v2.schemas.pack import PackIDType
from ninja import Schema

# ---------- Common ---------- #


# ---------- Requests ---------- #


class AnalyticsRequest(Schema):
    target: PackIDType | Literal["home"]


# ---------- Responses ---------- #
