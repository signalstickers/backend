from django.db import models


class Tag(models.Model):

    name = models.CharField(max_length=128, unique=True)

    class Meta:
        db_table = "tags"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        self.name = self.name.strip().lower()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
