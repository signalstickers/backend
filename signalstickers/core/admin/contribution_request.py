from core.models import ContributionRequest
from django.contrib import admin


@admin.register(ContributionRequest)
class ContributionRequestAdmin(admin.ModelAdmin):
    fields = ("id", "client_ip", "question", "request_date")
    readonly_fields = fields
