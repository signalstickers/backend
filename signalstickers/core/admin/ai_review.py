from core.models import AIReview
from django.contrib import admin


@admin.register(AIReview)
class AIReviewAdmin(admin.ModelAdmin):
    fields = (
        "pack",
        "status",
        "tags_match",
        "review_comment",
        "nsfw",
        "confidence",
        "alert",
    )
