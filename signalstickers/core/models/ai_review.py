from enum import Enum

from core.models.pack import Pack
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class AIReviewStatus(Enum):
    ACCEPT = "Accept"
    REFUSE = "Refuse"


class AIReview(models.Model):
    pack = models.OneToOneField(
        Pack,
        on_delete=models.CASCADE,
        related_name="ai_review",
    )
    status = models.CharField(
        max_length=10,
        choices=[(s.name, s.value) for s in AIReviewStatus],
        default=AIReviewStatus.REFUSE.name,
    )
    review_comment = models.TextField(
        blank=True,
        default="",
    )
    tags_match = models.BooleanField(
        default=False,
    )
    nsfw = models.BooleanField(
        default=False,
    )
    confidence = models.FloatField(
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
    )
    alert = models.BooleanField(
        default=True,
    )

    class Meta:
        db_table = "ai_reviews"

    def __str__(self):
        return f"AI review for {self.pack.title}"
