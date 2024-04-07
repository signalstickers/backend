from typing import Annotated

from ninja import Schema
from pydantic import UUID4, StringConstraints, model_validator

# ---------- Common ---------- #


# ---------- Requests ---------- #


class SecurityAnswerMixin:
    security_id: UUID4
    security_answer: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=200,
        ),
    ]


# ---------- Responses ---------- #


class SecurityQuestionMixin:
    security_id: UUID4
    security_question: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True,
            max_length=200,
        ),
    ]


class SecurityQuestionResponse(Schema, SecurityQuestionMixin):

    @model_validator(mode="before")
    @classmethod
    def shape_from_queryset(cls, data):

        return {
            "security_id": data.id,
            "security_question": data.question.question,
        }
