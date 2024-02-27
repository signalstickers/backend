from io import StringIO
import tempfile
from unittest.mock import patch

from core import utils
from core.models import Pack, PackAnimatedMode, PackStatus, Tag
from core.utils import get_current_ym_date, get_last_month_ym_date
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
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

        pack = Pack.objects.new(
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
        self.assertEqual(str(pack), self.testpack["title"])
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

        pack = Pack.objects.new(
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
            Pack.objects.new(
                pack_id="aaa",
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack id must"):
            Pack.objects.new(
                pack_id="A" * 32,
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(
            ValidationError, "The pack does not exists on Signal, or is invalid."
        ):
            Pack.objects.new(
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
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key="aaa",
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(ValidationError, "Pack key must"):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key="A" * 64,
                status=PackStatus.IN_REVIEW.name,
            )

        with self.assertRaisesRegex(
            ValidationError, "The pack does not exists on Signal, or is invalid."
        ):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key="a" * 64,
                status=PackStatus.IN_REVIEW.name,
            )

    def test_validation_pack_metadata(self, mocked_getpacklib):
        """
        Validation of the pack title, author and source (format)
        """

        with self.assertRaisesRegex(ValidationError, "Source too long"):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
                source="a" * 300,
            )

        mocked_getpacklib.return_value = TestPack("a" * 300, "b", b"\x00")

        with self.assertRaisesRegex(ValidationError, "Pack title too long"):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

        mocked_getpacklib.return_value = TestPack("a", "b" * 300, b"\x00")

        with self.assertRaisesRegex(ValidationError, "Author too long"):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
            )

    def test_validation_tags(self, _):
        """
        Validation of the pack source (format)
        """

        with self.assertRaisesRegex(ValidationError, "Too many tags"):
            Pack.objects.new(
                pack_id=self.testpack["pack_id"],
                pack_key=self.testpack["pack_key"],
                status=PackStatus.IN_REVIEW.name,
                tags=[str(i) for i in range(200)],
            )

    def test_tweeted(self, mocked_getpacklib):
        """
        Check tweet status
        """
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack_not_tweeted = Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            tweeted=False,
        )

        pack_tweeted = Pack.objects.new(
            pack_id="c" * 32,
            pack_key="d" * 64,
            status=PackStatus.ONLINE.name,
            tweeted=True,
        )

        pack_not_tweeted_inreview = Pack.objects.new(
            pack_id="e" * 32,
            pack_key="f" * 64,
            status=PackStatus.IN_REVIEW.name,
            tweeted=False,
        )

        packs = Pack.objects.not_twitteds()

        self.assertNotIn(pack_tweeted, packs)
        self.assertNotIn(pack_not_tweeted_inreview, packs)
        self.assertIn(pack_not_tweeted, packs)

    def test_animation_mode(self, mocked_getpacklib):
        """
        Test animation mode (forced, auto)
        """
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )

        self.assertFalse(pack.animated)
        self.assertEqual(pack.animated_mode, PackAnimatedMode.AUTO.name)

        # Force animated
        pack.animated_mode = PackAnimatedMode.FORCE_ANIMATED.name
        pack.clean()
        pack.save()
        self.assertTrue(pack.animated)

        # Force still
        pack.animated_mode = PackAnimatedMode.FORCE_STILL.name
        pack.clean()
        pack.save()
        self.assertFalse(pack.animated)

    def test_total_views(self, mocked_getpacklib):

        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        base_pack = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        self.assertEqual(base_pack.total_views, 0)

        base_pack.stats = {"a": 1, "b": 2}
        base_pack.save()
        self.assertEqual(base_pack.total_views, 3)

    def test_hot_views(self, mocked_getpacklib):

        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        base_pack = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        self.assertEqual(base_pack.hot_views, 0)

        base_pack.stats = {get_current_ym_date(): 5}
        base_pack.save()
        self.assertEqual(base_pack.hot_views, 5)

        base_pack.stats = {get_current_ym_date(): 5, get_last_month_ym_date(): 2}
        base_pack.save()
        self.assertEqual(base_pack.hot_views, 7)

        base_pack.stats = {
            "1979_01": 1,
            get_current_ym_date(): 5,
            get_last_month_ym_date(): 2,
        }
        base_pack.save()
        self.assertEqual(base_pack.hot_views, 7)

    def test_most_popular_for_month(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack_1 = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        pack_1.stats = {get_current_ym_date(): 5}
        pack_1.save()

        pack_2 = Pack.objects.new(
            pack_id="c" * 32, pack_key="d" * 64, status=PackStatus.ONLINE.name
        )
        pack_2.stats = {get_current_ym_date(): 10}
        pack_2.save()
        pack_3 = Pack.objects.new(
            pack_id="e" * 32, pack_key="f" * 64, status=PackStatus.ONLINE.name
        )
        pack_3.stats = {get_current_ym_date(): 1}
        pack_3.save()

        populars = Pack.objects.most_popular_for_month(get_current_ym_date())
        self.assertEqual(list(populars), [pack_2, pack_1, pack_3])

    def test_most_viewed_packs(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack_1 = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        pack_1.stats = {"2021_01": 2, get_current_ym_date(): 8}
        pack_1.save()

        pack_2 = Pack.objects.new(
            pack_id="c" * 32, pack_key="d" * 64, status=PackStatus.ONLINE.name
        )
        pack_2.stats = {"2020_08": 7, get_current_ym_date(): 2}
        pack_2.save()
        pack_3 = Pack.objects.new(
            pack_id="e" * 32, pack_key="f" * 64, status=PackStatus.ONLINE.name
        )
        pack_3.stats = {
            "2020_08": 1,
            "2020_09": 3,
            "2021_01": 12,
            get_current_ym_date(): 3,
        }
        pack_3.save()

        populars = Pack.objects.most_viewed_packs()
        self.assertEqual(
            list(populars),
            [
                {"pack": pack_3, "views": 19},
                {"pack": pack_1, "views": 10},
                {"pack": pack_2, "views": 9},
            ],
        )

    def test_total_packviews_for_month(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack_1 = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        pack_1.stats = {get_current_ym_date(): 1}
        pack_1.save()

        pack_2 = Pack.objects.new(
            pack_id="c" * 32, pack_key="d" * 64, status=PackStatus.ONLINE.name
        )
        pack_2.stats = {get_current_ym_date(): 2}
        pack_2.save()
        pack_3 = Pack.objects.new(
            pack_id="e" * 32, pack_key="f" * 64, status=PackStatus.ONLINE.name
        )
        pack_3.stats = {get_current_ym_date(): 3}
        pack_3.save()

        self.assertEqual(
            Pack.objects.total_packviews_for_month(get_current_ym_date()), 6
        )

    def test_total_packviews(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        pack_1 = Pack.objects.new(
            pack_id="a" * 32, pack_key="b" * 64, status=PackStatus.ONLINE.name
        )
        pack_1.stats = {"2021_01": 2, get_current_ym_date(): 1}
        pack_1.save()

        pack_2 = Pack.objects.new(
            pack_id="c" * 32, pack_key="d" * 64, status=PackStatus.ONLINE.name
        )
        pack_2.stats = {"2020_08": 7, get_current_ym_date(): 2}
        pack_2.save()
        pack_3 = Pack.objects.new(
            pack_id="e" * 32, pack_key="f" * 64, status=PackStatus.ONLINE.name
        )
        pack_3.stats = {
            "2020_08": 1,
            "2020_09": 3,
            "2021_01": 2,
            get_current_ym_date(): 3,
        }
        pack_3.save()

        self.assertEqual(
            Pack.objects.total_packviews(),
            {"2020_08": 8, "2020_09": 3, "2021_01": 4, get_current_ym_date(): 6},
        )

    def test_change_status_auto(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            self.testpack["title"], self.testpack["author"], b"\x00"
        )

        pack = Pack.objects.new(
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

        pack.approve()
        self.assertEqual(pack.status, PackStatus.ONLINE.name)

        pack.refuse()
        self.assertEqual(pack.status, PackStatus.REFUSED.name)


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
        # WebP
        self.assertFalse(
            utils.detect_animated_pack(
                TestPack(
                    "foo",
                    "bar",
                    b"\x52\x49\x46\x46\x46\xc9\x03\x00\x57\x45\x42\x50\x56\x50\x38\x58\x00\x00\x00\x00",
                    b"\x52\x49\x46\x46\x46\xc9\x03\x00\x57\x45\x42\x50\x56\x50\x38\x58\x99\x99\x99\x99",
                )
            )
        )

        # Animated WebP
        try:
            utils.detect_animated_pack(
                TestPack(
                    "foo",
                    "bar",
                    b"\x52\x49\x46\x46\x46\xc9\x03\x00\x57\x45\x42\x50\x56\x50\x38\x58\x00\x00\x00\x00\x41\x4e\x49\x4d",
                )
            )
            self.fail("Animated WebP")
        except ValidationError:
            pass


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class YmlImportCommandTest(TestCase):
    """
    Test the import_from_yml command
    """

    def test_import_stickers(self, mocked_getpacklib):
        """
        Test that stickers are correctly imported
        """
        mocked_getpacklib.return_value = TestPack("a", "b", b"\x00")
        out = StringIO()

        with tempfile.NamedTemporaryFile() as f_in:
            f_in.write(
                f"""\
{'a'*32}:
  key: {'b'*64}
  source: src
  tags:
    - Foo
    - Bar
  nsfw: true

{'c'*32}:
  key: {'d'*64}
  nsfw: False
  original: true
""".encode()
            )
            f_in.seek(0)

            call_command("import_from_yml", f_in.name, stdout=out)

        self.assertEqual(Pack.objects.count(), 2)

        # First pack
        pack_1 = Pack.objects.get(pack_id="a" * 32)
        self.assertEqual(pack_1.pack_key, "b" * 64)
        self.assertTrue(pack_1.nsfw)
        self.assertEqual(
            sorted([str(t) for t in pack_1.tags.all()]), sorted(["foo", "bar"])
        )

        # Second pack
        pack_2 = Pack.objects.get(pack_id="c" * 32)
        self.assertEqual(pack_2.pack_key, "d" * 64)
        self.assertEqual(pack_2.tags.count(), 0)
        self.assertTrue(pack_2.original)
        self.assertFalse(pack_2.nsfw)

    def test_import_stickers_duplicate(self, mocked_getpacklib):
        """
        Test that duplicate packs are not imported and reported
        """
        mocked_getpacklib.return_value = TestPack("a", "b", b"\x00")
        out = StringIO()

        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            nsfw=False,
            status=PackStatus.ONLINE.name,
        )

        with tempfile.NamedTemporaryFile() as f_in:
            f_in.write(
                f"""\
{'a'*32}:
  key: {'b'*64}
  nsfw: true
""".encode()
            )
            f_in.seek(0)

            call_command("import_from_yml", f_in.name, stdout=out)

        self.assertIn(f"{'a'*32} not imported (duplicate)", out.getvalue())
        self.assertIn("All done! Imported: 0", out.getvalue())
        self.assertEqual(Pack.objects.count(), 1)

        pack_in_db = Pack.objects.first()
        self.assertFalse(pack_in_db.nsfw)

    def test_import_stickers_invalid(self, mocked_getpacklib):
        """
        Test that invalid packs are not imported and reported
        """

        mocked_getpacklib.return_value = TestPack("a", "b", b"\x00")
        out = StringIO()

        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            nsfw=False,
            status=PackStatus.ONLINE.name,
        )

        mocked_getpacklib.return_value = None
        with tempfile.NamedTemporaryFile() as f_in:
            f_in.write(
                f"""\
{'a'*32}:
  key: {'b'*64}
  nsfw: true
""".encode()
            )
            f_in.seek(0)

            call_command("import_from_yml", f_in.name, stdout=out)

        self.assertIn(f"Pack {'a'*32} not imported (key: {'b'*64})", out.getvalue())


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class CleanPacksTagsCommandTest(TestCase):
    def test_command(self, mocked_getpacklib):
        """The Command should correctly remove, clean, delete tags"""
        mocked_getpacklib.return_value = TestPack(
            "Pack Pack", "Pack Pack author", b"\x00"
        )

        # Pack with malformed tags
        malformed_tag_name = [
            "#pastel #unicorn #flowers #pastel",
            "pastel",
            " #foo #bar",
        ]
        malformed_tags_pack = Pack.objects.new(
            pack_id="r" * 32,
            pack_key="r" * 64,
            status=PackStatus.ONLINE.name,
            tags=malformed_tag_name,
        )

        call_command("clean_packs_tags")

        # malformed tags should be cleaned (e.g: "#pastel #unicorn #flowers" should become three distinct tags)
        malformed_tags_pack.refresh_from_db()
        tags_names = [tag.name for tag in malformed_tags_pack.tags.all()]
        self.assertEqual(
            sorted(tags_names), ["bar", "flowers", "foo", "pastel", "unicorn"]
        )
        self.assertFalse(Tag.objects.filter(name=malformed_tag_name).exists())
