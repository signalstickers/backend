from http import HTTPStatus

from api_v2.schemas import AnalyticsRequest
from api_v2.schemas.errors import APIErrorResponse
from core.models import Pack, SiteStat
from core.utils import get_current_ym_date
from ninja import Form, Router

router = Router()


@router.post(
    "/",
    response={
        HTTPStatus.NO_CONTENT: None,
        HTTPStatus.BAD_REQUEST: APIErrorResponse,
    },
)
def send_analytics(request, data: Form[AnalyticsRequest]):
    """
    Analytics target route for the beacon
    """

    current_ym = get_current_ym_date()

    if data.target == "home":
        # Hit the homepage
        month_visit = SiteStat.objects.get_or_create(month=current_ym)[0]
        month_visit.visits += 1
        month_visit.save()
        return HTTPStatus.NO_CONTENT, None

    # Pack stats
    try:
        pack = Pack.objects.get(pack_id=data.target)
        try:
            pack.stats[current_ym] += 1
        except KeyError:
            pack.stats[current_ym] = 1
        pack.save()
        return HTTPStatus.NO_CONTENT, None
    except Pack.DoesNotExist:
        return HTTPStatus.BAD_REQUEST, APIErrorResponse(detail="Unknown pack")
