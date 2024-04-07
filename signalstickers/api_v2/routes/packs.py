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
from api_v2.utils import validate_securityanswer_or_die
from core.models import Pack, PackStatus, Report
from core.services import send_email_on_pack_propose
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
def get_all_packs(request, role_preload: bool = False):
    """
    List all packs.

    _Falsy_ values are ignored, and are not returned.

    If set to `true`, `role_preload` only returns the first 64 packs.
    """
    if role_preload:
        return Pack.objects.onlines()[:64]

    return Pack.objects.onlines()


@router.put(
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
        return HTTPStatus.BAD_REQUEST, APIErrorResponse(
            detail="An error happened.",
        )

    except IntegrityError:
        return HTTPStatus.BAD_REQUEST, APIErrorResponse(
            detail=(
                "This pack already exists, or has already been proposed "
                "(and is waiting for its approval)"
            )
        )

    logger.info("Created new pack (from contribution): %s", pack.title)
    send_email_on_pack_propose(pack)
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
    Propose a new pack. This route can be called from third-party applications.

    Contact us to obtain an API token:
    [https://github.com/signalstickers/backend/issues](https://github.com/signalstickers/backend/issues)
    """
    return HTTPStatus.NOT_IMPLEMENTED, None


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
        return HTTPStatus.NOT_FOUND, APIErrorResponse(
            detail=(
                "Unknown pack. Check that the signal.art URL is correct, "
                "and that you submitted your pack on signalstickers.org."
            ),
        )

    return StatusResponse(
        pack_title=pack.title,
        pack_id=pack.pack_id,
        status=PackStatus[pack.status],
        status_comments=(
            pack.status_comments
            if PackStatus[pack.status] == PackStatus.REFUSED
            else None
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
        return HTTPStatus.NOT_FOUND, APIErrorResponse(detail="Unknown pack")

    Report.objects.create(
        content=data.content,
        pack=pack,
    )

    return HTTPStatus.NO_CONTENT, None
