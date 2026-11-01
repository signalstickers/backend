import logging

from api_v2.routes import (
    aireview_router,
    analytics_router,
    packs_router,
    security_router,
)
from api_v2.schemas.errors import APIError
from django.conf import settings
from django.http import Http404, JsonResponse
from ninja import NinjaAPI

logger = logging.getLogger(__name__)

app_name = "api_v2"

api_v2 = NinjaAPI(
    title="signalstickers.org API",
    description=(
        "This API is intended to be used exclusively by signalstickers' front-end. "
        "If you are building an app on top of it, please contact us! 🤗"
    ),
    version="2.0",
    urls_namespace="api_v2",
    openapi_url="openapi.json" if settings.DEBUG else None,
    docs_url="docs" if settings.DEBUG else None,
    openapi_extra={
        "info": {
            "termsOfService": "https://signalstickers.org/about#terms-of-service",
        }
    },
)


@api_v2.exception_handler(APIError)
def api_error_handler(request, exc):
    return JsonResponse(
        {"detail": [{"type": exc.error_type, "loc": exc.loc, "msg": str(exc.message)}]},
        status=exc.status_code,
    )


@api_v2.exception_handler(Http404)
def not_found_handler(request, _exc):
    return JsonResponse(
        {"detail": [{"type": "not_found", "loc": [], "msg": "Not Found"}]},
        status=404,
    )


@api_v2.exception_handler(Exception)
def internal_error_handler(request, _exc):
    logger.exception("Unhandled exception in API v2")
    return JsonResponse(
        {
            "detail": [
                {"type": "internal_error", "loc": [], "msg": "Internal Server Error"}
            ]
        },
        status=500,
    )


api_v2.add_router("admin", aireview_router, tags=["Admin"])
api_v2.add_router("packs", packs_router, tags=["Packs"])
api_v2.add_router("security-question", security_router, tags=["Security"])
api_v2.add_router("analytics", analytics_router, tags=["Analytics"])
