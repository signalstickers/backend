from unittest.mock import patch

from core.models import Pack, PackStatus
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class StatusTestCase(TestCase):
    def test_status_ok(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        pack = Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            source="Source 1",
            nsfw=True,
            original=False,
            submitter_comments="",
            tags=["Foo1", "BAR1", "FooBar1"],
            api_via="TestClient 1",
        )

        response = self.client.post(
            reverse("api_v1:packstatus"),
            {"pack_id": "a" * 32, "pack_key": "b" * 64},
            content_type="application/json",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(
            response.data,
            {
                "error": "",
                "pack_title": pack.title,
                "pack_id": pack.pack_id,
                "status": PackStatus.ONLINE.name,
                "status_comments": "",
            },
        )

    def test_status_pack_noexists(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            source="Source 1",
            nsfw=True,
            original=False,
            submitter_comments="",
            tags=["Foo1", "BAR1", "FooBar1"],
            api_via="TestClient 1",
        )

        response = self.client.post(
            reverse("api_v1:packstatus"),
            {"pack_id": "d" * 32, "pack_key": "e" * 64},
            content_type="application/json",
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(
            response.data,
            {
                "error": "Unknown pack. Check that the signal.art URL is correct, "
                "and that you submitted your pack on signalstickers."
            },
        )

    def test_status_badrequest(self, _):

        response = self.client.post(
            reverse("api_v1:packstatus"),
            {"pack_id": "d" * 33, "pack_key": "e" * 64},
            content_type="application/json",
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data, {"error": "Bad request."})

        response = self.client.post(
            reverse("api_v1:packstatus"),
            {"pack_id": "d" * 32, "pack_key": "e" * 63},
            content_type="application/json",
        )
        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data, {"error": "Bad request."})
