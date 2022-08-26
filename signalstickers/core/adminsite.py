from core.views import AdminStatsView, AdminTriggerActionsView
from django.contrib.admin import AdminSite
from django.urls import path


class CustomAdmin(AdminSite):

    site_url = None

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
