from django.contrib import admin

from apps.api.models import ApiKey, BotPreventionQuestion, ContributionRequest


@admin.register(BotPreventionQuestion)
class BotPreventionQuestionAdmin(admin.ModelAdmin):
    # Add help texts for some fields
    def get_form(self, request, obj=None, **kwargs):
        kwargs.update({"help_texts": {"answer": "Must match [a-zA-Z0-9]+"}})
        return super().get_form(request, obj, **kwargs)


@admin.register(ContributionRequest)
class ContributionRequestAdmin(admin.ModelAdmin):
    fields = ("id", "client_ip", "question", "request_date")
    readonly_fields = fields


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    fields = ("name", "key")
