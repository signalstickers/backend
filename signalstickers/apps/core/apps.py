from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = "core"


from django.contrib.admin.apps import AdminConfig


class CustomAdmin(AdminConfig):
    default_site = "apps.core.admin.CustomAdmin"

