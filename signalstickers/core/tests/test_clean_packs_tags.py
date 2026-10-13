from unittest.mock import patch

from core.models import Pack, PackStatus, Tag
from django.core.management import call_command
from django.test import TestCase

from signalstickers.tests_common import TestPack


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
