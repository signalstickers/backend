from unittest.mock import patch

from core.models import Pack, PackStatus
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class PackTestCase(TestCase):
    def test_get_all_packs(self, mocked_getpacklib):
        """
        Test for the API path that returns all the ONLINE packs
        """

        # First pack, status ONLINE: should be returned last by the API
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
            submitter_comments="Not visible in the API1",
            tags=["Foo1", "BAR1", "FooBar1"],
            api_via="TestClient 1",
        )

        # Second pack, status ONLINE: should be returned second by the API
        mocked_getpacklib.return_value = TestPack(
            "Pack title 2", "Pack author 2", b"\x61\x63\x54\x4c"
        )

        Pack.objects.new(
            pack_id="c" * 32,
            pack_key="d" * 64,
            status=PackStatus.ONLINE.name,
            source="Source 2",
            nsfw=False,
            original=True,
            submitter_comments="Not visible in the API2",
            tags=["Foo2", "CBAR2", "CFooBar2"],
            api_via="TestClient 2",
        )

        # Third pack, status ONLINE: should be returned first by the API
        mocked_getpacklib.return_value = TestPack(
            "Pack title 2", "Pack author 2", b"\x00"
        )
        Pack.objects.new(
            pack_id="e" * 32,
            pack_key="f" * 64,
            status=PackStatus.ONLINE.name,
            source="",
            nsfw=False,
            original=False,
            submitter_comments="Not visible in the API3",
            tags=[],
            api_via="",
        )

        # Status IN_REVIEW: should NOT be returned by the API
        Pack.objects.new(
            pack_id="g" * 32, pack_key="h" * 64, status=PackStatus.IN_REVIEW.name
        )
        response = self.client.get(reverse("api_v1:packs"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            response.data,
            [
                {
                    "meta": {"id": "e" * 32, "key": "f" * 64},
                    "manifest": {
                        "title": "Pack title 2",
                        "author": "Pack author 2",
                        "cover": {"id": 42},
                    },
                },
                {
                    "meta": {
                        "id": "c" * 32,
                        "key": "d" * 64,
                        "source": "Source 2 (via TestClient 2)",
                        "tags": ["cbar2", "cfoobar2", "foo2"],
                        "original": True,
                        "animated": True,
                    },
                    "manifest": {
                        "title": "Pack title 2",
                        "author": "Pack author 2",
                        "cover": {"id": 42},
                    },
                },
                {
                    "meta": {
                        "id": "a" * 32,
                        "key": "b" * 64,
                        "source": "Source 1 (via TestClient 1)",
                        "tags": ["bar1", "foo1", "foobar1"],
                        "nsfw": True,
                    },
                    "manifest": {
                        "title": "Pack title 1",
                        "author": "Pack author 1",
                        "cover": {"id": 42},
                    },
                },
            ],
        )

    def test_pack_cleanup(self, mocked_getpacklib):
        """Furry packs should not include any other tags than 'Furry'"""
        mocked_getpacklib.return_value = TestPack(
            "Pack Furry", "Pack Furry author", b"\x00"
        )

        # Furry pack with forbidden keywords
        Pack.objects.new(
            pack_id="t" * 32,
            pack_key="t" * 64,
            status=PackStatus.ONLINE.name,
            tags=["furry", "sexy", "cute"],
        )

        response = self.client.get(reverse("api_v1:packs"))
        expected_tag = ["furry"]
        self.assertEqual(
            response.data,
            [
                {
                    "meta": {"id": "t" * 32, "key": "t" * 64, "tags": expected_tag},
                    "manifest": {
                        "title": "Pack Furry",
                        "author": "Pack Furry author",
                        "cover": {"id": 42},
                    },
                }
            ],
        )
