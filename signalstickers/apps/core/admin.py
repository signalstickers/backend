from django.contrib.admin import AdminSite
from django.urls import path

from .views import AdminTriggerActionsView


class CustomAdmin(AdminSite):
    def get_urls(self):
        urls = super().get_urls()

        my_urls = [
            path("trigger_actions/", self.admin_view(AdminTriggerActionsView.as_view()))
        ]

        urls += my_urls
        return urls
