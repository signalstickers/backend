"""
Regression test: API v2 routes must not use a trailing slash.

django-ninja generates one URL pattern per route. We iterate over every
pattern the API exposes and assert none of them ends with a ``/``. The only
exceptions are the non-endpoint infrastructure routes (the API root and the
OpenAPI/Swagger docs), which are not part of the public contract.
"""

from api_v2.urls import api_v2
from django.test import SimpleTestCase

# Routes that are not API endpoints and are exempt from the no-trailing-slash
# rule: the API root (``/v2/``) and the dev-only OpenAPI/Swagger docs.
INFRASTRUCTURE_ROUTES = {"api-root", "openapi-json", "openapi-view"}


class NoTrailingSlashTestCase(SimpleTestCase):
    def test_no_route_has_a_trailing_slash(self):
        patterns, _app_name, _namespace = api_v2.urls

        endpoint_patterns = [
            pattern for pattern in patterns if pattern.name not in INFRASTRUCTURE_ROUTES
        ]

        # Sanity check: we must actually be inspecting the API routes, not an
        # empty list (which would make the test pass vacuously).
        self.assertGreater(len(endpoint_patterns), 0)

        for pattern in endpoint_patterns:
            with self.subTest(route=pattern.name):
                path = str(pattern.pattern)
                self.assertFalse(
                    path.endswith("/"),
                    f"Route {pattern.name!r} resolves to {path!r}, "
                    "which has a trailing slash",
                )
