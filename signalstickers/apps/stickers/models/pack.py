import re
from base64 import b64encode

from apps.stickers.utils import detect_animated_pack, get_pack_from_signal
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Prefetch, prefetch_related_objects

from .pack_animated_mode import PackAnimatedMode
from .pack_status import PackStatus
from .tag import Tag


class PackManager(models.Manager):
    def onlines(self):
        """
        Return only packs "ONLINE", last packs first.
        """

        return (
            Pack.objects.filter(status=PackStatus.ONLINE.name)
            .order_by("-id")
            .prefetch_related("tags")
        )

    def not_twitteds(self):
        """
        Return pack that have not been tweeted
        """
        return Pack.objects.filter(
            status=PackStatus.ONLINE.name, tweeted=False
        ).order_by("-id")


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
    title = models.CharField(max_length=128)  # computed
    author = models.CharField(max_length=128)  # computed
    id_cover = models.IntegerField(default=0)

    # Metadata
    source = models.CharField(max_length=128, blank=True)
    nsfw = models.BooleanField(default=False, verbose_name="NSFW")
    original = models.BooleanField(default=False)
    tags = models.ManyToManyField("stickers.tag", blank=True, related_name="packs")

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

    # Review
    status = models.CharField(
        max_length=60,
        choices=[(status.name, status.value) for status in PackStatus],
        default=PackStatus.IN_REVIEW.name,
    )
    status_comments = models.TextField(blank=True)
    submitter_comments = models.TextField(blank=True)
    tweeted = models.BooleanField(default=False)

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

        if len(self.source) > 128:
            raise ValidationError("Source too long.")

        # Pack verification
        pack = get_pack_from_signal(self.pack_id, self.pack_key)
        if not pack:
            raise ValidationError("Pack does not exists on Signal: wrong id or key?")

        self.title = pack.title
        self.author = pack.author
        self.id_cover = pack.cover.id

        if len(self.title) > 128:
            raise ValidationError("Pack title too long.")

        if len(self.author) > 128:
            raise ValidationError("Author too long.")

        # Animation
        # self.animated_detected = detect_animated_pack(pack)
        self.animated_detected = False
        if self.animated_mode == PackAnimatedMode.AUTO.name:
            self.animated = self.animated_detected
        elif self.animated_mode == PackAnimatedMode.FORCE_ANIMATED.name:
            self.animated = True
        else:
            self.animated = False

    @property
    def stickers_preview(self):
        """
        Return a list of all stickers image data and their emoji. Used for
        viewing packs in the admin panel.
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
