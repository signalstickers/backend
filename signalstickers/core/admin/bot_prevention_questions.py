from core.models import BotPreventionQuestion
from django.contrib import admin


@admin.register(BotPreventionQuestion)
class BotPreventionQuestionAdmin(admin.ModelAdmin):
    # Add help texts for some fields
    def get_form(self, request, obj=None, **kwargs):  # pylint: disable=arguments-differ
        kwargs.update({"help_texts": {"answer": "Must match [a-zA-Z0-9]+"}})
        return super().get_form(request, obj, **kwargs)
