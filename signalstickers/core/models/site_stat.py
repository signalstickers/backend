from django.db import models


class SiteStatsManager(models.Manager):
    def get_visits_by_month(self):
        return {
            data["month"]: data["visits"]
            for data in SiteStat.objects.all()
            .order_by("month")
            .values("month", "visits")
        }


class SiteStat(models.Model):
    objects = SiteStatsManager()

    # Stats
    month = models.CharField(max_length=7)  # YYYY_MM
    visits = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "sitestats"
        default_permissions = ()

    def __str__(self):
        return f"Stats for {self.month}"
