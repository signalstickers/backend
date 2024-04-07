from api_v2.schemas import SecurityQuestionResponse
from core.services import new_contribution_request
from django.conf import settings
from django.http import HttpRequest
from ninja import Router

router = Router()


@router.post(
    "/",
    response={
        200: SecurityQuestionResponse,
    },
)
def generate_security_question(request: HttpRequest):
    return new_contribution_request(request.META.get(settings.HEADER_IP))
