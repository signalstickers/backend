from api_v2.schemas.pack import PackMetaRequest
from api_v2.schemas.securityquestion import SecurityAnswerMixin
from ninja import Schema
from pydantic import StringConstraints
from typing_extensions import Annotated

# ---------- Common ---------- #


# ---------- Requests ---------- #


class ContributionRequest(Schema, SecurityAnswerMixin):
    pack: PackMetaRequest
    submitter_comments: Annotated[
        str,
        StringConstraints(max_length=400),
    ] = ""


# ---------- Responses ---------- #
