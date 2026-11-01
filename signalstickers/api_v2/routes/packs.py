from http import HTTPStatus
import logging

from api_v2.schemas import (
    APIErrorResponse,
    ContributionRequest,
    PackIdentifierRequest,
    PackResponse,
    ReportRequest,
    StatusResponse,
)
from api_v2.schemas.errors import APIError
from api_v2.utils import validate_securityanswer_or_die
from core.models import Pack, PackStatus, Report
from core.notifications import NotificationPriority, notify
from core.services import send_email_on_pack_propose
from core.utils import admin_url
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from ninja import Query, Router

logger = logging.getLogger(__name__)


router = Router()


@router.get(
    "/",
    response={
        HTTPStatus.OK: list[PackResponse],
    },
    exclude_none=True,
    exclude_defaults=True,
)
def get_all_packs(request, limit: int | None = Query(None, ge=1)):
    """
    List all packs.

    _Falsy_ values are ignored, and are not returned.

    If set, `limit` returns only the first `limit` packs (most recent first).
    """
    packs = Pack.objects.onlines()
    if limit is not None:
        if limit != 64:
            raise APIError(400, "invalid_limit", "Unauthorized limit")
        packs = packs[:limit]
    return packs


@router.post(
    "/",
    response={
        HTTPStatus.NO_CONTENT: None,
        HTTPStatus.BAD_REQUEST: APIErrorResponse,
        HTTPStatus.NOT_FOUND: APIErrorResponse,
    },
    summary="Propose a new pack",
)
def contribute(request, data: ContributionRequest):
    """
    Propose a new pack. Requires a security-question.
    """

    validate_securityanswer_or_die(
        data.security_id,
        data.security_answer,
        request.META.get(settings.HEADER_IP),
    )

    # Create pack in review
    try:
        pack = Pack.objects.new(
            pack_id=data.pack.id,
            pack_key=data.pack.key,
            status=PackStatus.IN_REVIEW.name,
            source=data.pack.source,
            nsfw=data.pack.nsfw,
            original=data.pack.original,
            tags=data.pack.tags,
            submitter_comments=data.submitter_comments,
        )
    except ValidationError:
        raise APIError(400, "pack_invalid", "An error happened.") from None

    except IntegrityError:
        raise APIError(
            400,
            "duplicate_pack",
            "This pack already exists, or has already been proposed "
            "(and is waiting for its approval)",
            loc=["body", "data", "pack", "id"],
        ) from None

    logger.info("Created new pack (from contribution): %s", pack.title)
    send_email_on_pack_propose(pack)
    notify(
        "signalstickers-packs",
        "New pack proposed",
        f"New pack proposed: {pack.title} by {pack.author}",
        priority=NotificationPriority.MIN,
        click_url=admin_url(),
    )
    return HTTPStatus.NO_CONTENT, None


@router.put(
    "/from-third-party",
    response={
        HTTPStatus.NOT_IMPLEMENTED: None,
    },
    summary="Third-party API: propose a new pack",
    deprecated=True,
)
def public_contribute(
    request,
):
    """
    Third-party contribution is intentionally not available in API v2.
    Third parties must keep using API v1 (`PUT /v1/contribute/` with `X-Auth-Token`).
    """
    raise APIError(
        501,
        "not_implemented",
        "Third-party contribution is not available in API v2. Use API v1.",
    )


@router.get(
    "/status",
    response={
        HTTPStatus.OK: StatusResponse,
        HTTPStatus.NOT_FOUND: APIErrorResponse,
    },
    summary="Get the status of a pack",
)
def get_pack_status(request, data: Query[PackIdentifierRequest]):
    """
    Get the status of a pack
    """

    try:
        pack = Pack.objects.get(
            pack_id=data.id,
            pack_key=data.key,
        )
    except Pack.DoesNotExist:
        raise APIError(
            404,
            "unknown_pack",
            "Unknown pack. Check that the signal.art URL is correct, "
            "and that you submitted your pack on signalstickers.org.",
            loc=["query", "id"],
        ) from None

    pack_status = PackStatus[pack.status]
    # Escalated packs are still in the review process, from the submitter's
    # point of view
    if pack_status == PackStatus.ESCALATED:
        pack_status = PackStatus.IN_REVIEW

    return StatusResponse(
        pack_title=pack.title,
        pack_id=pack.pack_id,
        status=pack_status,
        status_comments=(
            pack.status_comments if pack_status == PackStatus.REFUSED else None
        ),
    )


@router.post(
    "/report",
    response={
        HTTPStatus.NO_CONTENT: None,
        HTTPStatus.BAD_REQUEST: APIErrorResponse,
        HTTPStatus.NOT_FOUND: APIErrorResponse,
    },
    summary="Report a pack to admins",
)
def report(request, data: ReportRequest):
    """
    Report a pack to signalstickers' admins. Requires a security-question.
    """

    validate_securityanswer_or_die(
        data.security_id,
        data.security_answer,
        request.META.get(settings.HEADER_IP),
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

    Report.objects.create(
        content=data.content,
        pack=pack,
    )

    notify(
        "signalstickers-packs",
        "Pack reported",
        f"Pack reported: {pack.title}",
        priority=NotificationPriority.HIGH,
        click_url=admin_url(),
    )

    return HTTPStatus.NO_CONTENT, None
