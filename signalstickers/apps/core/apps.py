from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class CoreConfig(AppConfig):
    name = "core"


class CustomAdmin(AdminConfig):
    default_site = "apps.core.admin.CustomAdmin"
