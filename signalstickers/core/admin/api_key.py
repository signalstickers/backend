from core.models import ApiKey
from django.contrib import admin


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    fields = ("name", "key")
