from ninja import Schema
from ninja.errors import HttpError


class APIErrorResponse(Schema):
    detail: str


class InvalidSecurityErrorResponse(HttpError):
    pass
