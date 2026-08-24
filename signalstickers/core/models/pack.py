from base64 import b64encode
import re

from core.models.pack_animated_mode import PackAnimatedMode
from core.models.pack_manager import PackManager
from core.models.pack_status import PackStatus
from core.utils import (
    detect_animated_pack,
    get_current_ym_date,
    get_last_month_ym_date,
    get_pack_from_signal,
)
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models

PACK_ID_REGEX = r"^[a-z0-9]{32}$"
PACK_ID_ERROR = "Pack id must be 32, lowercase and numbers."
PACK_KEY_REGEX = r"^[a-z0-9]{64}$"
PACK_KEY_ERROR = "Pack key must be 64, lowercase and numbers."


def _resolve_animated_mode(animated_mode, animated_detected):
    """
    Return the final animated status of a pack, based on its animated mode
    and whether animation was detected in its stickers.
    """
    if animated_mode == PackAnimatedMode.AUTO.name:
        return animated_detected
    if animated_mode == PackAnimatedMode.FORCE_ANIMATED.name:
        return True
    return False


class Pack(models.Model):
    objects = PackManager()

    # Pack info
    pack_id = models.CharField(
        max_length=32,
        unique=True,
        validators=[
            RegexValidator(
                regex=PACK_ID_REGEX,
                message=PACK_ID_ERROR,
                code="nomatch",
            )
        ],
    )
    pack_key = models.CharField(
        max_length=64,
        validators=[
            RegexValidator(
                regex=PACK_KEY_REGEX,
                message=PACK_KEY_ERROR,
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
        if not re.match(PACK_ID_REGEX, self.pack_id):
            raise ValidationError(PACK_ID_ERROR)

        if not re.match(PACK_KEY_REGEX, self.pack_key):
            raise ValidationError(PACK_KEY_ERROR)

        if len(self.source) > 256:
            raise ValidationError("Source too long.")

        # Pack verification
        pack = get_pack_from_signal(self.pack_id, self.pack_key)
        if not pack:
            raise ValidationError("The pack does not exists on Signal, or is invalid.")

        self.title = pack.title
        self.author = pack.author
        self.id_cover = pack.cover.id

        if len(self.title) > 256:
            raise ValidationError("Pack title too long.")

        if len(self.author) > 256:
            raise ValidationError("Author too long.")

        # Animation
        self.animated_detected = detect_animated_pack(pack)
        self.animated = _resolve_animated_mode(
            self.animated_mode, self.animated_detected
        )

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
