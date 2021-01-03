from django.apps import AppConfig
from django.contrib.admin import apps


class CoreConfig(AppConfig):
    name = "core"


class CustomAdmin(apps.AdminConfig):
    default_site = "core.adminsite.CustomAdmin"
