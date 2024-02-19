from enum import Enum

from core.models.pack import Pack
from django.db import models


class ReportManager(models.Manager):

    def to_process(self):
        return Report.objects.filter(status="TO_PROCESS")

    def to_process_count(self):
        return Report.objects.to_process().count()


class ReportStatus(Enum):
    TO_PROCESS = "To process"
    AGREED = "Agreed"
    DISAGREED = "Disagreed"


class Report(models.Model):
    objects = ReportManager()

    pack = models.ForeignKey(Pack, on_delete=models.PROTECT)
    content = models.TextField(blank=True)
    date = models.DateTimeField(auto_now_add=True, blank=True)
    status = models.CharField(
        max_length=60,
        choices=[(status.name, status.value) for status in ReportStatus],
        default=ReportStatus.TO_PROCESS.name,
    )

    class Meta:
        db_table = "reports"

    def __str__(self):
        return str(self.date)
