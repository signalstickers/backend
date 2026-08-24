from core.models.pack_status import PackStatus
from core.models.tag import Tag
from django.db import models
from django.db.models import Prefetch, Sum
from django.db.models.expressions import RawSQL


class PackManager(models.Manager):
    def onlines(self):
        """
        Return only packs "ONLINE", last packs first.
        """
        return (
            self.model.objects.filter(status=PackStatus.ONLINE.name)
            .order_by("-id")
            .prefetch_related(
                Prefetch("tags", queryset=Tag.objects.all().order_by("name"))
            )
        )

    def in_review(self):
        """
        Return packs with status "IN REVIEW".
        """
        return self.model.objects.filter(status="IN_REVIEW")

    def in_review_with_tags(self):
        """
        Return IN_REVIEW packs with tags prefetched (alphabetically ordered).
        """
        return self.model.objects.filter(
            status=PackStatus.IN_REVIEW.name
        ).prefetch_related(
            Prefetch("tags", queryset=Tag.objects.all().order_by("name"))
        )

    def in_review_count(self):
        """
        Return packs count with status "IN REVIEW".
        """
        return self.model.objects.in_review().count()

    def escalated(self):
        """
        Return packs with status "ESCALATED".
        """
        return self.model.objects.filter(status="ESCALATED")

    def escalated_count(self):
        """
        Return packs count with status "ESCALATED".
        """
        return self.model.objects.escalated().count()

    def most_popular_for_month(self, month, nbr=10):
        """
        Return the top `nbr` packs for a given `month` (YYYY_MM)
        """
        return (
            self.model.objects.filter(stats__has_key=month)
            .annotate(stats_month=RawSQL("stats->%s", (month,)))
            .order_by("-stats_month")[:nbr]
        )

    def total_packviews_for_month(self, month):
        """
        Return the total pack views for a given `month` (YYYY_MM)
        """
        return (
            self.model.objects.filter(stats__has_key=month)
            .annotate(views_month=RawSQL("(stats->%s)::INTEGER", (month,)))
            .aggregate(Sum("views_month"))["views_month__sum"]
        )

    def most_viewed_packs(self, nbr=10):
        """
        Return the `nbr` most viewed packs ever
        """
        # TODO do this with aggregation in DB
        packs = self.model.objects.all()
        all_packs_sumviews = []
        for pack in packs:
            all_packs_sumviews.append({"pack": pack, "views": sum(pack.stats.values())})

        return sorted(all_packs_sumviews, key=lambda k: k["views"], reverse=True)[:nbr]

    def total_packviews(self):
        """
        Return pack views by month for all month
        """
        # TODO do this with aggregation in DB
        stats = self.model.objects.all().values("stats")
        stats_month = {}
        for pack_stats in stats:
            for month, stats in pack_stats["stats"].items():
                if month in stats_month:
                    stats_month[month] += stats
                else:
                    stats_month[month] = stats
        return stats_month

    def new(
        self,
        pack_id,
        pack_key,
        status,
        source="",
        nsfw=False,
        original=False,
        submitter_comments="",
        tags=None,
        api_via="",
        editorschoice=False,
    ):
        """
        Create a new pack with validation, save it, and return it. Use this
        function instead of create(), as this one also create related tags
        properly. Return the pack which has been created.
        """
        from core.services.pack_factory import (  # pylint: disable=import-outside-toplevel,cyclic-import
            create_pack,
        )

        return create_pack(
            pack_id=pack_id,
            pack_key=pack_key,
            status=status,
            source=source,
            nsfw=nsfw,
            original=original,
            submitter_comments=submitter_comments,
            tags=tags,
            api_via=api_via,
            editorschoice=editorschoice,
        )
