from core.services import notify_admin_login
from core.views import AdminStatsView, AdminTriggerActionsView
from django.conf import settings
from django.contrib.admin import AdminSite
from django.urls import path


class CustomAdmin(AdminSite):

    site_url = None

    def login(self, request, extra_context=None):
        response = super().login(request, extra_context=extra_context)
        if request.user.is_authenticated and response.status_code in (200, 302):
            client_ip = request.META.get(settings.HEADER_IP)
            notify_admin_login(request.user.username, client_ip)
        return response

    def get_urls(self):
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
