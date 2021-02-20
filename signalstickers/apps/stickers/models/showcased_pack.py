from django.db import models

from .pack import Pack


class ShowcasedPack(models.Model):

    pack = models.ForeignKey(Pack, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0, blank=False, null=False)

    class Meta(object):
        ordering = ["order"]

    def __str__(self):
        return self.pack.title
