from core import utils
from django.core.exceptions import ValidationError
from django.test import TestCase

from signalstickers.tests_common import TestPack


class UtilsTestCase(TestCase):
    def test_detect_animated_pack(self):

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x61\x63\x54\x4c", b"\x61\x63\x54\x4c")
            )
        )

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x61\x63\x54\x4c", b"\x47\x49\x46\x38\x39\x61")
            )
        )

        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x00\x00\x00\x00", b"\x47\x49\x46\x38\x39\x61")
            )
        )
        self.assertTrue(
            utils.detect_animated_pack(
                TestPack("foo", "bar", b"\x00\x00\x00\x00", b"\x61\x63\x54\x4c")
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
