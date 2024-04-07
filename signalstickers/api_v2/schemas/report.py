from typing import Annotated

from api_v2.schemas.pack import PackIDType
from api_v2.schemas.securityquestion import SecurityAnswerMixin
from ninja import Schema
from pydantic import StringConstraints

# ---------- Common ---------- #


# ---------- Requests ---------- #


class ReportRequest(Schema, SecurityAnswerMixin):

    pack_id: PackIDType
    content: Annotated[
        str,
        StringConstraints(
            min_length=30,
            max_length=2000,
        ),
    ]


# ---------- Responses ---------- #
