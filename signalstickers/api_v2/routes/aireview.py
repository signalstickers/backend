from http import HTTPStatus
import logging

from api_v2.schemas import (
    AIReviewRequest,
    APIErrorResponse,
    InReviewPackResponse,
)
from api_v2.schemas.errors import APIError
from core.models import AIReview, Pack
from django.conf import settings
from ninja import Router

logger = logging.getLogger(__name__)

router = Router()


def _check_ai_auth(request) -> bool:
    api_key = request.headers.get("X-Auth-Token")
    return bool(api_key) and api_key == settings.AI_REVIEW_API_KEY


@router.get(
    "/toreview",
    response={
        HTTPStatus.OK: list[InReviewPackResponse],
        HTTPStatus.UNAUTHORIZED: APIErrorResponse,
    },
    summary="List the packs to review",
)
def get_in_review_packs(request, only_noaireview: bool = False):
    """
    List the IN_REVIEW packs (for the AI review bot).

    If `only_noaireview` is true, only the packs without an AI review yet
    are returned.
    """
    if not _check_ai_auth(request):
        raise APIError(
            401, "unauthorized", "Unauthorized", loc=["header", "X-Auth-Token"]
        )

    packs = Pack.objects.in_review_with_tags().order_by("id")
    if only_noaireview:
        packs = packs.filter(ai_review__isnull=True)
    return packs


@router.put(
    "/aireview",
    response={
        HTTPStatus.NO_CONTENT: None,
        HTTPStatus.UNAUTHORIZED: APIErrorResponse,
        HTTPStatus.NOT_FOUND: APIErrorResponse,
    },
    summary="Upsert the AI review of a pack",
)
def update_ai_review(request, data: AIReviewRequest):
    """
    Upsert the AI review of a pack (for the AI review bot).
    """
    if not _check_ai_auth(request):
        raise APIError(
            401, "unauthorized", "Unauthorized", loc=["header", "X-Auth-Token"]
        )

    try:
        pack = Pack.objects.get(pack_id=data.pack_id)
    except Pack.DoesNotExist:
        raise APIError(
            404,
            "unknown_pack",
            "Unknown pack",
            loc=["body", "data", "pack_id"],
        ) from None

    _, created = AIReview.objects.update_or_create(
        pack=pack,
        defaults={
            "status": data.status.name,
            "review_comment": data.review_comment,
            "nsfw": data.nsfw,
            "tags_match": data.tags_match,
            "confidence": data.confidence,
            "alert": data.alert,
        },
    )

    logger.info(
        "AI review %s for pack %s",
        "created" if created else "updated",
        pack.pack_id,
    )
    return HTTPStatus.NO_CONTENT, None
