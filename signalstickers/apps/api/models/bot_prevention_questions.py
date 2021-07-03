from django.core.validators import RegexValidator
from django.db import models


class BotPreventionQuestion(models.Model):

    question = models.CharField(max_length=128)
    answer = models.CharField(
        max_length=128,
        validators=[RegexValidator(
            regex="^[a-zA-Z0-9]+$",
            message="The answer must be alphanumeric -- No special characters allowed."
        )]
    )

    class Meta:
        db_table = "botpreventionquestions"

    def __str__(self):
        return self.question
