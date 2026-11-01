from ninja import Schema
from ninja.errors import HttpError


class APIErrorDetail(Schema):
    type: str
    loc: list[str] = []
    msg: str


class APIErrorResponse(Schema):
    detail: list[APIErrorDetail]


class APIError(HttpError):
    def __init__(
        self,
        status_code: int,
        error_type: str,
        msg: str,
        loc: list[str] | None = None,
    ):
        super().__init__(status_code, msg)
        self.error_type = error_type
        self.loc = loc or []
