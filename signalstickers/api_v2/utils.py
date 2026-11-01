from api_v2.schemas.errors import APIError
from core.services import check_contribution_request
from pydantic import IPvAnyAddress

WRONG_ANSWER = "Wrong answer"


def validate_securityanswer_or_die(
    security_id: str, security_answer: str, client_ip: IPvAnyAddress
):
    is_cont_req_valid, sec_quest_invalid_reason = check_contribution_request(
        security_id,
        security_answer,
        client_ip,
    )
    if not is_cont_req_valid:
        if sec_quest_invalid_reason == WRONG_ANSWER:
            raise APIError(
                400,
                "wrong_answer",
                WRONG_ANSWER,
                loc=["body", "data", "security_answer"],
            )
        raise APIError(
            400,
            "security_verification_failed",
            sec_quest_invalid_reason,
            loc=["body", "data", "security_id"],
        )
