from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase

from . import utils
from .models import PackAnimatedMode, PackStatus
from .services import new_pack


class TestSticker:
    def __init__(self, id, img_data):
        self.id = id
        self.image_data = img_data


class TestPack:
    def __init__(self, title, author, *args):
        self.title = title
        self.author = author
        self.cover = TestSticker(42, b"\x00")
        self.stickers = [TestSticker(id + 1, arg) for id, arg in enumerate(args)]


@patch("apps.stickers.models.pack.get_pack_from_signal", autospec=True)
class PackTestCase(TestCase):
    def setUp(self):

        self.testpack = {
            "pack_id": "4830e258138fca961ab2151d9596755c",
            "pack_key": "87078ee421bad8bf44092ca72166b67ae5397e943452e4300ced9367b7f6a1a1",
            "title": "Foo title",
            "author": "Bar author",
            "id_cover": 42,
            "source": "foobar.com",
            "nsfw": False,
            "original": True,
            "submitter_comments": "Howdy",
            "tags": ["Foo", "Bar", "Foobar"],
        }

    def test_pack_creation_no_via(self, mocked_getpacklib):
        """
        Packs are created correctly
        """

        mocked_getpacklib.return_value = TestPack(
            self.testpack["title"], self.testpack["author"], b"\x00"
        )

        pack = new_pack(
            pack_id=self.testpack["pack_id"],
            pack_key=self.testpack["pack_key"],
            status=PackStatus.IN_REVIEW.name,
            source=self.testpack["source"],
            nsfw=self.testpack["nsfw"],
            original=self.testpack["original"],
            submitter_comments=self.testpack["submitter_comments"],
            tags=self.testpack["tags"],
            api_via="",
            tweeted=False,
        )

        self.assertEqual(pack.pack_id, self.testpack["pack_id"])
        self.assertEqual(pack.pack_key, self.testpack["pack_key"])
        self.assertEqual(pack.title, self.testpack["title"])
        self.assertEqual(pack.author, self.testpack["author"])
        self.assertEqual(pack.id_cover, self.testpack["id_cover"])
        self.assertEqual(pack.source, self.testpack["source"])
        self.assertEqual(pack.nsfw, self.testpack["nsfw"])
        self.assertEqual(pack.original, self.testpack["original"])
        self.assertEqual(pack.animated, False)
        self.assertEqual(pack.submitter_comments, self.testpack["submitter_comments"])
        self.assertFalse(pack.animated_detected)
        self.assertEqual(pack.animated_mode, PackAnimatedMode.AUTO.name)
        self.assertEqual(
            sorted([str(t) for t in pack.tags.all()]),
            sorted([t.lower() for t in self.testpack["tags"]]),
        )

    def test_pack_creation_with_via(self, mocked_getpacklib):
        """
        Packs with "via" are created correctly
        """

        mocked_getpacklib.return_value = TestPack(
            self.testpack["title"], self.testpack["author"], b"\x00"
        )

        pack = new_pack(
            pack_id=self.testpack["pack_id"],
            pack_key=self.testpack["pack_key"],
            status=PackStatus.IN_REVIEW.name,
            source=self.testpack["source"],
            nsfw=self.testpack["nsfw"],
            original=self.testpack["original"],
            submitter_comments=self.testpack["submitter_comments"],
            tags=self.testpack["tags"],
            api_via="foo",
            tweeted=False,
        )

        self.assertEqual(pack.source, f'{self.testpack["source"]} (via foo)')

    def test_validation_pack_id(self, mocked_getpacklib):
        """
        Validation of the pack_id (format, existance on Signal's server)
        """

        mocked_getpacklib.return_value = None

        with self.assertRaisesRegex(ValidationError, "Pack id must"):
            new_pack(
                pack_id="aaa",
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack id must"):
            new_pack(
                pack_id="A" * 32,
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack does not exists on Signal"):
            new_pack(
                pack_id="a" * 32,
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

    def test_validation_pack_key(self, mocked_getpacklib):
        """
        Validation of the pack_key (format, existance on Signal's server)
        """

        mocked_getpacklib.return_value = None

        with self.assertRaisesRegex(ValidationError, "Pack key must"):
            new_pack(
                pack_id=self.testpack["pack_id"],
                pack_key="aaa",
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack key must"):
            new_pack(
                pack_id=self.testpack["pack_id"],
                pack_key="A" * 64,
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack does not exists on Signal"):
            new_pack(
                pack_id=self.testpack["pack_id"],
                pack_key="a" * 64,
                status=PackStatus.IN_REVIEW.name,
            )

    def test_validation_pack_source(self, mocked_getpacklib):
        """
        Validation of the pack source (format)
        """

        mocked_getpacklib.return_value = None

        with self.assertRaisesRegex(ValidationError, "Source too long"):
            new_pack(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
                source="a" * 130,
            )

    def test_validation_tags(self, mocked_getpacklib):
        """
        Validation of the pack source (format)
        """

        mocked_getpacklib.return_value = None

        with self.assertRaisesRegex(ValidationError, "Too many tags"):
            new_pack(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
                tags=[str(i) for i in range(200)],
            )


class UtilsTestCase(TestCase):
    def test_detect_animated_pack(self):

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x61\x63\x54\x4C", b"\x61\x63\x54\x4C")
            )
        )

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x61\x63\x54\x4C", b"\x47\x49\x46\x38\x39\x61")
            )
        )

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x00\x00\x00\x00", b"\x47\x49\x46\x38\x39\x61")
            )
        )
        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x00\x00\x00\x00", b"\x61\x63\x54\x4C")
            )
        )
        self.assertFalse(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x00\x00\x00\x00", b"\x99\x99\x99\x99")
            )
        )

