import re
from base64 import b64encode

from apps.stickers.utils import detect_animated_pack, get_pack_from_signal
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models, transaction
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
            Pack.objects.filter(status=PackStatus.ONLINE.name).order_by("-id")
            # .prefetch_related("tags")
            .prefetch_related(
                Prefetch("tags", queryset=Tag.objects.all().order_by("name"))
            )
        )

    def not_twitteds(self):
        """
        Return pack that have not been tweeted
        """
        return Pack.objects.filter(
            status=PackStatus.ONLINE.name, tweeted=False
        ).order_by("-id")

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
    def stickers_preview(self):
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
