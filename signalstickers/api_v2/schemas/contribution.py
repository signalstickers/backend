from api_v2.schemas.pack import PackMetaRequest
from api_v2.schemas.securityquestion import SecurityAnswerMixin
from ninja import Schema
from pydantic import ConfigDict, StringConstraints
from typing_extensions import Annotated

# ---------- Common ---------- #


# ---------- Requests ---------- #


class APIContributionRequest(Schema):
    pack: PackMetaRequest

    # Allow to discriminate with ContributionRequest
    model_config = ConfigDict(extra="forbid")


class ContributionRequest(Schema, SecurityAnswerMixin):
    pack: PackMetaRequest
    submitter_comments: Annotated[
        str,
        StringConstraints(max_length=400),
    ]


# ---------- Responses ---------- #
