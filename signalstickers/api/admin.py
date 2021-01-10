from django.contrib import admin

from api.models import ApiKey, BotPreventionQuestion, ContributionRequest


@admin.register(BotPreventionQuestion)
class BotPreventionQuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(ContributionRequest)
class ContributionRequestAdmin(admin.ModelAdmin):
    fields = ("id", "client_ip", "question", "request_date")
    readonly_fields = fields


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    fields = ("name", "key")
