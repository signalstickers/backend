import uuid

from django.db import models


class ApiKey(models.Model):

    key = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128)

    class Meta:
        db_table = "apikeys"

    def __str__(self):
        return f"API key for {self.name}"
