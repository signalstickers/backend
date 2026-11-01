from http import HTTPStatus
import logging
from unittest.mock import patch

from core.models import Pack, PackStatus
from django.test import TestCase
from django.urls import reverse

from signalstickers.tests_common import TestPack

logging.disable(logging.CRITICAL)


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class PackTestCase(TestCase):
    def _create_online_packs(self, mocked_getpacklib):
        """
        Create 3 ONLINE packs (returned most recent first: e, c, a) and
        1 IN_REVIEW pack (not returned by the API).
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

    def test_get_all_packs(self, mocked_getpacklib):
        """
        Test for the API path that returns all the ONLINE packs
        """
        self._create_online_packs(mocked_getpacklib)

        response = self.client.get(reverse("api_v2:get_all_packs"))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")
        self.assertEqual(
            response.json(),
            [
                {
                    "meta": {"id": "e" * 32, "key": "f" * 64},
                    "manifest": {
                        "title": "Pack title 2",
                        "author": "Pack author 2",
                        "cover_id": 42,
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
                        "cover_id": 42,
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
                        "cover_id": 42,
                    },
                },
            ],
        )

    def test_get_all_packs_with_limit(self, mocked_getpacklib):
        """
        ?limit=64 returns only the first 64 packs (most recent first)
        """
        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")
        for i in range(65):
            Pack.objects.new(
                pack_id=format(i, "x").rjust(32, "0"),
                pack_key=format(i, "x").rjust(64, "0"),
                status=PackStatus.ONLINE.name,
            )

        response = self.client.get(reverse("api_v2:get_all_packs"), {"limit": 64})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(len(response.json()), 64)
        # The oldest pack (lowest id) is not returned
        self.assertNotIn("0" * 32, [pack["meta"]["id"] for pack in response.json()])

    def test_get_all_packs_limit_too_small(self, _):
        """
        ?limit=0 is invalid (must be >= 1)
        """
        response = self.client.get(reverse("api_v2:get_all_packs"), {"limit": 0})

        self.assertEqual(response.status_code, HTTPStatus.UNPROCESSABLE_ENTITY)

    def test_get_all_packs_limit_not_64(self, _):
        """
        ?limit=2 is invalid (only 64 is allowed)
        """
        response = self.client.get(reverse("api_v2:get_all_packs"), {"limit": 2})

        self.assertEqual(response.status_code, HTTPStatus.BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "invalid_limit",
                        "loc": [],
                        "msg": "Unauthorized limit",
                    }
                ]
            },
        )

    def test_pack_cleanup(self, mocked_getpacklib):
        """Furry packs should not include any other tags than 'Furry'"""
        mocked_getpacklib.return_value = TestPack(
            "Pack Furry", "Pack Furry author", b"\x00"
        )

        # Furry pack with forbidden keywords
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            tags=["furry", "foo", "bar"],
        )

        response = self.client.get(reverse("api_v2:get_all_packs"))
        expected_tag = ["furry"]
        self.assertEqual(
            response.json(),
            [
                {
                    "meta": {"id": "a" * 32, "key": "b" * 64, "tags": expected_tag},
                    "manifest": {
                        "title": "Pack Furry",
                        "author": "Pack Furry author",
                        "cover_id": 42,
                    },
                }
            ],
        )
