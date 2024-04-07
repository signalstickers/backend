from http import HTTPStatus
from unittest.mock import patch

from core.models import Pack, PackStatus
from django.test import TestCase
from django.urls import reverse

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class StatusAPITestCase(TestCase):

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

        response = self.client.get(
            reverse("api_v2:get_pack_status"),
            {"id": "a" * 32, "key": "b" * 64},
            content_type="application/json",
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "pack_title": pack.title,
                "pack_id": pack.pack_id,
                "status": PackStatus.ONLINE.name,
                "status_comments": None,
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

        response = self.client.get(
            reverse("api_v2:get_pack_status"),
            {"id": "d" * 32, "key": "e" * 64},
            content_type="application/json",
        )

        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": "Unknown pack. Check that the signal.art URL is correct, "
                "and that you submitted your pack on signalstickers.org."
            },
        )

    def test_status_badrequest(self, _):

        response = self.client.get(
            reverse("api_v2:get_pack_status"),
            {"id": "d" * 33, "key": "e" * 64},
            content_type="application/json",
        )
        self.assertEqual(HTTPStatus.UNPROCESSABLE_ENTITY, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "ctx": {"max_length": 32},
                        "loc": ["query", "id"],
                        "msg": "String should have at most 32 characters",
                        "type": "string_too_long",
                    }
                ]
            },
        )

        response = self.client.get(
            reverse("api_v2:get_pack_status"),
            {"id": "d" * 32, "key": "e" * 63},
            content_type="application/json",
        )
        self.assertEqual(HTTPStatus.UNPROCESSABLE_ENTITY, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "ctx": {"min_length": 64},
                        "loc": ["query", "key"],
                        "msg": "String should have at least 64 characters",
                        "type": "string_too_short",
                    }
                ]
            },
        )
