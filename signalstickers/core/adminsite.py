import logging

from core.notifications import NotificationPriority, notify
from django.conf import settings
from django.contrib.admin import AdminSite
from django.urls import path

logger = logging.getLogger("main")


class CustomAdmin(AdminSite):

    site_url = None

    def login(self, request, extra_context=None):
        response = super().login(request, extra_context=extra_context)
        if request.user.is_authenticated and response.status_code in (200, 302):
            client_ip = request.META.get(settings.HEADER_IP)
            logger.info("Admin login: %s from %s", request.user.username, client_ip)
            notify(
                "signalstickers-admin",
                "Admin login",
                f"Admin '{request.user.username}' logged in from {client_ip}",
                priority=NotificationPriority.DEFAULT,
                tags=["lock"],
                click_url=f"https://{settings.ALLOWED_HOSTS[0]}/{settings.ADMIN_URL}",
            )
        return response

    def get_urls(self):
        # Imported here (not at module level) to avoid a circular import:
        # core.admin's @admin.register triggers the import of this module.
        # pylint: disable=import-outside-toplevel
        from core.admin.views import AdminStatsView, AdminTriggerActionsView

        urls = super().get_urls()
        my_urls = [
            path(
                "trigger_actions/",
                self.admin_view(AdminTriggerActionsView.as_view()),
                {"admin_site": self},
                name="trigger_actions",
            ),
            path(
                "stats/",
                self.admin_view(AdminStatsView.as_view()),
                {"admin_site": self},
                name="stats",
            ),
        ]

        urls = my_urls + urls
        return urls
