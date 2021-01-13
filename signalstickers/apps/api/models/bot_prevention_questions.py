from django.db import models


class BotPreventionQuestion(models.Model):

    question = models.CharField(max_length=128)
    answer = models.CharField(max_length=128)

    class Meta:
        db_table = "botpreventionquestions"

    def __str__(self):
        return self.question
