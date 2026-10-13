from io import StringIO
import tempfile
from unittest.mock import patch

from core.models import Pack, PackStatus
from django.core.management import call_command
from django.test import TestCase

from signalstickers.tests_common import TestPack


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
            f_in.write(f"""\
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
""".encode())
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
            f_in.write(f"""\
{'a'*32}:
  key: {'b'*64}
  nsfw: true
""".encode())
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
            f_in.write(f"""\
{'a'*32}:
  key: {'b'*64}
  nsfw: true
""".encode())
            f_in.seek(0)

            call_command("import_from_yml", f_in.name, stdout=out)

        self.assertIn(f"Pack {'a'*32} not imported (key: {'b'*64})", out.getvalue())
