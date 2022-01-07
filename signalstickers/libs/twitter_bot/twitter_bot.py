#!/usr/bin/python3
# pylint: disable=too-many-locals
from io import BytesIO
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import anyio
from django.conf import settings
from signalstickers_client import StickersClient
import tweepy


async def _get_pack(pack_id, pack_key):
    """
    Returns a Pack object (from signalstickers-client )
    """
    async with StickersClient() as client:
        pack = await client.get_pack(pack_id, pack_key)
    return pack


class PackPreview:
    def __init__(self, nsfw=False):
        self.nb_stickers: int

        self.thumbs = []

        self.nsfw = nsfw
        self.preview_light = None
        self.preview_dark = None

        self.line_height = 180
        self.sticker_width = 180  # with border
        self.image_sticker_width = 160  # the image
        self.max_stickers_per__line = None

    def add_image(self, image_bytes):
        self.thumbs.append(image_bytes)

    def create(self):

        self.nb_stickers = len(self.thumbs)

        height = 2 * self.line_height

        if self.nb_stickers <= 5:
            self.max_stickers_per__line = 2
        elif self.nb_stickers == 6:
            self.max_stickers_per__line = 3
        elif self.nb_stickers in [7, 8]:
            self.max_stickers_per__line = 4
        else:  # nb_stickers >= 9
            self.max_stickers_per__line = 5

        if self.nb_stickers == 2:
            height = self.line_height
        if self.nb_stickers == 5:
            height = 3 * self.line_height

        if self.nb_stickers % 2 == 0 or self.nb_stickers > 10:
            # Add additionnal height for signalstickers logo at the bottom
            height = height + 120

        image = Image.new(
            "RGB",
            (self.max_stickers_per__line * self.sticker_width + 20, height),
            (255, 255, 255),
        )

        preview_light_img = self._create(image)

        bytes_preview_light = BytesIO()
        preview_light_img.save(bytes_preview_light, "PNG")
        bytes_preview_light.seek(0)
        self.preview_light = bytes_preview_light

        image = Image.new(
            "RGB",
            (self.max_stickers_per__line * self.sticker_width + 20, height),
            (18, 18, 18),
        )
        preview_dark_img = self._create(image)

        bytes_preview_dark = BytesIO()
        preview_dark_img.save(bytes_preview_dark, "PNG")
        bytes_preview_dark.seek(0)
        self.preview_dark = bytes_preview_dark

    def _create(self, image):

        current_stickers_on_line = 0
        current_line = 0

        font_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "OpenSans-Bold.ttf"
        )
        with open(font_path, "rb") as font_file:
            open_sans = ImageFont.truetype(font_file, size=50)

        for index, thumb in enumerate(self.thumbs):

            if index == 9 and self.nb_stickers > 10:
                break

            current_thumb = Image.open(BytesIO(thumb)).convert("RGBA")
            current_thumb.thumbnail(
                (self.image_sticker_width, self.image_sticker_width)
            )

            image.paste(
                current_thumb,
                (
                    current_stickers_on_line * self.sticker_width + 10,
                    current_line * self.line_height + 10,
                ),
                current_thumb,
            )
            current_stickers_on_line += 1

            if current_stickers_on_line == self.max_stickers_per__line:
                current_stickers_on_line = 0
                current_line += 1

        if self.nsfw:
            image = image.filter(ImageFilter.GaussianBlur(12))

        # Add the "+ [n]" if more than 10 stickers
        if self.nb_stickers > 10:
            plus_text = ImageDraw.Draw(image)
            plus_text.text(
                (4 * self.sticker_width + 20, self.line_height + 65),
                f"+ {self.nb_stickers - 9}",
                font=open_sans,
                fill=(180, 180, 180),
            )

        signalstickers_logo_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "signalstickers_sticker.png"
        )

        signalstickers_logo = Image.open(signalstickers_logo_path)
        signalstickers_logo.thumbnail((50, 50))
        # Add the "signalstickers" logo

        if self.nb_stickers in [3, 5, 7, 9]:
            # add as the last sticker
            line_height = (
                2 * self.line_height if self.nb_stickers == 5 else self.line_height
            )

            image.paste(
                signalstickers_logo,
                (
                    (self.max_stickers_per__line - 1) * self.sticker_width + 65,
                    line_height + 63,
                ),
                signalstickers_logo,
            )
        else:
            # Add at the bottom
            line_nb = 1 if self.nb_stickers == 2 else 2
            image.paste(
                signalstickers_logo,
                (
                    int(image.width / 2 - signalstickers_logo.width / 2),
                    line_nb * self.line_height + 30,
                ),
                signalstickers_logo,
            )

        return image


def tweet_pack(django_pack):

    # Set Twitter API
    auth = tweepy.OAuthHandler(
        settings.TWITTER_CONF["consumer_key"], settings.TWITTER_CONF["consumer_secret"]
    )
    auth.set_access_token(
        settings.TWITTER_CONF["access_token"],
        settings.TWITTER_CONF["access_token_secret"],
    )
    twitter_api = tweepy.API(auth)

    # Get the current pack object (from signalstickers-client)
    pack_sst_cli = anyio.run(_get_pack, django_pack.pack_id, django_pack.pack_key)

    # Create preview
    pack_preview = PackPreview(django_pack.nsfw)
    for sticker in pack_sst_cli.stickers:
        pack_preview.add_image(sticker.image_data)
    pack_preview.create()

    # Set tweet content
    content_nsfw = "\n⚠️ This pack is NSFW 🔞\n" if django_pack.nsfw else ""
    content_original = "\n✨ This pack is original ✨\n" if django_pack.original else ""
    content_animated = "\n 🎡 This pack is animated! 🎡\n" if django_pack.animated else ""
    content_hashtag = (
        "\n\n#makeprivacystick" if "twitter" not in django_pack.source else ""
    )

    tweet_text = f"""New stickers for Signal!

"{pack_sst_cli.title}" by {pack_sst_cli.author}
{content_animated}{content_original}{content_nsfw}
🖼 {pack_sst_cli.nb_stickers} stickers
➡️ https://signalstickers.com/pack/{pack_sst_cli.id}{content_hashtag}
    """

    media_ids = []
    res = twitter_api.media_upload("preview_light.png", file=pack_preview.preview_light)
    media_ids.append(res.media_id)

    res = twitter_api.media_upload("preview_dark.png", file=pack_preview.preview_dark)
    media_ids.append(res.media_id)

    # Tweet with multiple images
    main_tweet = twitter_api.update_status(status=tweet_text, media_ids=media_ids)

    # Post 2nd tweet

    tags_list = [tag.name for tag in django_pack.tags.all()[:10]]

    tags = f"🏷️ Tags: {', '.join(tags_list)}\n" if tags_list else ""

    source = f"🔎 Source: {django_pack.source}\n" if django_pack.source else ""

    more_info_text = f"{tags}{source}ℹ️ Direct link: https://signal.art/addstickers/#pack_id={pack_sst_cli.id}&pack_key={pack_sst_cli.key}"

    twitter_api.update_status(more_info_text, in_reply_to_status_id=main_tweet.id)
