from http import HTTPStatus

from api_v2.schemas.errors import InvalidSecurityErrorResponse
from core.services import check_contribution_request
from pydantic import IPvAnyAddress


def validate_securityanswer_or_die(
    security_id: str, security_answer: str, client_ip: IPvAnyAddress
):
    is_cont_req_valid, sec_quest_invalid_reason = check_contribution_request(
        security_id,
        security_answer,
        client_ip,
    )
    if not is_cont_req_valid:
        raise InvalidSecurityErrorResponse(
            HTTPStatus.BAD_REQUEST,
            sec_quest_invalid_reason,
        )
