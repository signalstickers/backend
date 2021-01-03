from base64 import b64encode

from django.core.exceptions import ValidationError
from django.db import models
from stickers.utils import detect_animated_pack, get_pack_from_signal

from .pack_animated_mode import PackAnimatedMode
from .pack_status import PackStatus


class Pack(models.Model):

    # Pack info
    pack_id = models.CharField(max_length=32, unique=True)
    pack_key = models.CharField(max_length=64)
    title = models.CharField(max_length=128)  # computed
    author = models.CharField(max_length=128)  # computed

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

    class Meta:
        db_table = "packs"

    def __str__(self):
        return self.title

    def clean(self):

        # Basic validation
        if len(self.pack_id) != 32:
            raise ValidationError("Id shoud be 32 chars long.")
        if len(self.pack_key) != 64:
            raise ValidationError("Key shoud be 64 chars long.")

        # Pack verification
        pack = get_pack_from_signal(self.pack_id, self.pack_key)
        if not pack:
            raise ValidationError("Pack does not exists: wrong id or key.")

        self.title = pack.title
        self.author = pack.author

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
        """
        stickers = []  # contains dict {emoji, img}
        pack = get_pack_from_signal(self.pack_id, self.pack_key)

        for sticker in pack.stickers:
            stickers.append(
                {"emoji": sticker.emoji, "img": b64encode(sticker.image_data).decode()}
            )

        return stickers
