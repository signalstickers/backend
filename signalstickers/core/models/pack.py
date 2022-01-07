from base64 import b64encode
import re

from core.models.pack_animated_mode import PackAnimatedMode
from core.models.pack_status import PackStatus
from core.models.tag import Tag
from core.utils import (
    detect_animated_pack,
    get_current_ym_date,
    get_last_month_ym_date,
    get_pack_from_signal,
)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
from django.db.models import Prefetch, Sum
from django.db.models.expressions import RawSQL


class PackManager(models.Manager):
    def onlines(self):
        """
        Return only packs "ONLINE", last packs first.
        """
        return (
            Pack.objects.filter(status=PackStatus.ONLINE.name).order_by("-id")
            # .prefetch_related("tags")
            .prefetch_related(
                Prefetch("tags", queryset=Tag.objects.all().order_by("name"))
            )
        )

    def in_review_count(self):
        """
        Return packs count with status "IN REVIEW".
        """
        return Pack.objects.filter(status="IN_REVIEW").count()

    def not_twitteds(self):
        """
        Return pack that have not been tweeted
        """
        return Pack.objects.filter(
            status=PackStatus.ONLINE.name, tweeted=False
        ).order_by("-id")

    def most_popular_for_month(self, month, nbr=10):
        """
        Return the top `nbr` packs for a given `month` (YYYY_MM)
        """
        return (
            Pack.objects.filter(stats__has_key=month)
            .annotate(stats_month=RawSQL("stats->%s", (month,)))
            .order_by("-stats_month")[:nbr]
        )

    def total_packviews_for_month(self, month):
        """
        Return the total pack views for a given `month` (YYYY_MM)
        """
        return (
            Pack.objects.filter(stats__has_key=month)
            .annotate(views_month=RawSQL("(stats->%s)::INTEGER", (month,)))
            .aggregate(Sum("views_month"))["views_month__sum"]
        )

    def most_viewed_packs(self, nbr=10):
        """
        Return the `nbr` most viewed packs ever
        """
        # TODO do this with aggregation in DB
        packs = Pack.objects.all()
        all_packs_sumviews = []
        for pack in packs:
            all_packs_sumviews.append({"pack": pack, "views": sum(pack.stats.values())})

        return sorted(all_packs_sumviews, key=lambda k: k["views"], reverse=True)[:nbr]

    def total_packviews(self):
        """
        Return pack views by month for all month
        """
        # TODO do this with aggregation in DB
        stats = Pack.objects.all().values("stats")
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
        tweeted=False,
        editorschoice=False,
    ):
        """
        Create a new pack with validation, save it, and return it. Use this
        function instead of create(), as this one also create related tags
        properly. Return the pack which has been created.
        """

        if api_via:
            source = source.strip() + f" (via {api_via})"
        else:
            source = source.strip()

        tags = tags or []
        if len(tags) > 40:
            raise ValidationError("Too many tags (max 40).")

        pack = Pack(
            pack_id=pack_id.strip(),
            pack_key=pack_key.strip(),
            source=source,
            status=status,
            nsfw=nsfw,
            original=original,
            submitter_comments=submitter_comments,
            tweeted=tweeted,
            editorschoice=editorschoice,
        )

        pack.clean()

        with transaction.atomic():
            pack.save()

            tags_obj_list = []
            for tag in tags:
                tag_obj, _ = Tag.objects.get_or_create(name=tag.lower())
                tags_obj_list.append(tag_obj)

            if tags_obj_list:
                pack.tags.add(*tags_obj_list)

        return pack


class Pack(models.Model):
    objects = PackManager()

    # Pack info
    pack_id = models.CharField(
        max_length=32,
        unique=True,
        validators=[
            RegexValidator(
                regex="^[a-z0-9]{32}$",
                message="Pack id must be 32, lowercase and numbers.",
                code="nomatch",
            )
        ],
    )
    pack_key = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(
                regex="^[a-z0-9]{64}$",
                message="Pack key must be 64, lowercase and numbers.",
                code="nomatch",
            )
        ],
    )
    title = models.CharField(max_length=256)  # computed
    author = models.CharField(max_length=256)  # computed
    id_cover = models.IntegerField(default=0)

    # Metadata
    source = models.CharField(max_length=256, blank=True)
    nsfw = models.BooleanField(default=False, verbose_name="NSFW")
    original = models.BooleanField(default=False)
    editorschoice = models.BooleanField("Editor's choice", default=False)
    tags = models.ManyToManyField("core.tag", blank=True, related_name="packs")

    # Animation
    animated = models.BooleanField(
        default=False
    )  # computed, the final animated status that will be displayed to users.
    animated_detected = models.BooleanField(default=False)  # computed
    animated_mode = models.CharField(
        max_length=30,
        choices=[(mode.name, mode.value) for mode in PackAnimatedMode],
        default=PackAnimatedMode.AUTO.name,
    )

    # Stats
    stats = models.JSONField(default=dict, blank=True, null=True)

    # Review
    status = models.CharField(
        max_length=60,
        choices=[(status.name, status.value) for status in PackStatus],
        default=PackStatus.IN_REVIEW.name,
    )
    status_comments = models.TextField(blank=True)
    submitter_comments = models.TextField(blank=True)
    tweeted = models.BooleanField(default=False)

    @property
    def total_views(self):
        """
        Return the total number of views for the current pack
        TODO do this with aggregation in DB
        """
        return sum(self.stats.values())

    @property
    def hot_views(self):
        """
        Return the number of views from this month and last month for the
        current pack
        TODO do this with aggregation in DB
        """
        this_month_views = self.stats.get(get_current_ym_date(), 0)
        last_month_views = self.stats.get(get_last_month_ym_date(), 0)
        return this_month_views + last_month_views

    class Meta:
        db_table = "packs"

    def __str__(self):
        return self.title

    def clean(self):

        # Basic validation
        if not re.match(r"^[a-z0-9]{32}$", self.pack_id):
            raise ValidationError("Pack id must be 32, lowercase and numbers.")

        if not re.match(r"^[a-z0-9]{64}$", self.pack_key):
            raise ValidationError("Pack key must be 64, lowercase and numbers.")

        if len(self.source) > 256:
            raise ValidationError("Source too long.")

        # Pack verification
        pack = get_pack_from_signal(self.pack_id, self.pack_key)
        if not pack:
            raise ValidationError("Pack does not exists on Signal: wrong id or key?")

        self.title = pack.title
        self.author = pack.author
        self.id_cover = pack.cover.id

        if len(self.title) > 256:
            raise ValidationError("Pack title too long.")

        if len(self.author) > 256:
            raise ValidationError("Author too long.")

        # Animation
        self.animated_detected = detect_animated_pack(pack)
        if self.animated_mode == PackAnimatedMode.AUTO.name:
            self.animated = self.animated_detected
        elif self.animated_mode == PackAnimatedMode.FORCE_ANIMATED.name:
            self.animated = True
        else:
            self.animated = False

    @property
    def stickers_preview(self):  # pragma: no cover
        """
        Return a list of all stickers image data and their emoji. Used for
        viewing packs in the admin panel.
        TODO cache the images
        """
        stickers = []  # contains dict {emoji, img}
        pack = get_pack_from_signal(self.pack_id, self.pack_key)

        if not pack:
            return {}

        for sticker in pack.stickers:
            stickers.append(
                {"emoji": sticker.emoji, "img": b64encode(sticker.image_data).decode()}
            )

        return stickers

    def get_model_name(self):
        return self._meta.model_name

    def approve(self):
        self.status = PackStatus.ONLINE.name
        self.save()

    def refuse(self):
        self.status = PackStatus.REFUSED.name
        self.save()
