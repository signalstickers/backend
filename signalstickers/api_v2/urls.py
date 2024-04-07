from api_v2.routes import analytics_router, packs_router, security_router
from ninja import NinjaAPI

app_name = "api_v2"

api_v2 = NinjaAPI(
    title="signalstickers.org API",
    description=(
        "This API is intended to be used exclusively by signalstickers' front-end. "
        "If you are building an app on top of it, please contact us! 🤗"
    ),
    version="2.0-beta1",
    urls_namespace="api_v2",
    openapi_extra={
        "info": {
            "termsOfService": "https://signalstickers.org/about#terms-of-service",
        }
    },
)

api_v2.add_router("packs", packs_router, tags=["Packs"])
api_v2.add_router("security-question", security_router, tags=["Security"])
api_v2.add_router("analytics", analytics_router, tags=["Analytics"])
