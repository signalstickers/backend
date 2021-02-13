import logging
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from apps.api.models import BotPreventionQuestion
from apps.api.services import new_contribution_request
from apps.stickers.models import Pack, PackAnimatedMode, PackStatus
from apps.stickers.services import new_pack


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
class APITestCase(TestCase):
    def setUp(self):
        q = BotPreventionQuestion(question="foo", answer="bar")
        q.save()

    def test_get_all_packs(self, mocked_getpacklib):
        """
        Test for the API path that returns all the ONLINE packs
        """

        # First pack, status ONLINE: should be returned last by the API
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        new_pack(
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

        # Second pack, status ONLINE: should be returned first by the API
        mocked_getpacklib.return_value = TestPack(
            "Pack title 2", "Pack author 2", b"\x61\x63\x54\x4C"
        )

        new_pack(
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

        # Status IN_REVIEW: should NOT be returned by the API
        new_pack(pack_id="e" * 32, pack_key="f" * 64, status=PackStatus.IN_REVIEW.name)
        response = self.client.get(reverse("packs"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")
        self.assertEqual(
            [
                {
                    "meta": {
                        "id": "c" * 32,
                        "key": "d" * 64,
                        "source": "Source 2 (via TestClient 2)",
                        "tags": ["cbar2", "cfoobar2", "foo2"],
                        "nsfw": False,
                        "original": True,
                        "animated": True,
                    },
                    "manifest": {
                        "title": "Pack title 2",
                        "author": "Pack author 2",
                        "cover": {"id": 42},
                    },
                    "status": "ONLINE",
                },
                {
                    "meta": {
                        "id": "a" * 32,
                        "key": "b" * 64,
                        "source": "Source 1 (via TestClient 1)",
                        "tags": ["bar1", "foo1", "foobar1"],
                        "nsfw": True,
                        "original": False,
                        "animated": False,
                    },
                    "manifest": {
                        "title": "Pack title 1",
                        "author": "Pack author 1",
                        "cover": {"id": 42},
                    },
                    "status": "ONLINE",
                },
            ],
            response.data,
        )

    def test_propose_pack_(self, mocked_getpacklib):
        """
        Valid Pack request
        """
        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        contrib_req = new_contribution_request("10.0.0.42")

        response = self.client.put(
            reverse("packs"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "source.example.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)
        self.assertEqual(1, len(Pack.objects.all()))
        self.assertEqual(0, len(Pack.objects.onlines()))

        pack = Pack.objects.get()

        self.assertEqual(pack.status, PackStatus.IN_REVIEW.name)
        self.assertEqual(pack.pack_id, "a" * 32)
        self.assertEqual(pack.pack_key, "b" * 64)
        self.assertEqual(pack.title, "Pack title")
        self.assertEqual(pack.author, "Pack author")
        self.assertEqual(pack.id_cover, 42)
        self.assertEqual(pack.source, "source.example.com")
        self.assertEqual(pack.nsfw, True)
        self.assertEqual(pack.original, False)
        self.assertEqual(
            sorted([str(t) for t in pack.tags.all()]), sorted(["foo", "bar", "foobar"])
        )
        self.assertEqual(pack.submitter_comments, "Thanks")

    def test_propose_pack_invalid_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with invalid/expired contributionrequest should not be
        accepted
        """
        logging.disable(logging.CRITICAL)
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        response = self.client.put(
            reverse("packs"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": "6c7ab3b4-59cf-423a-a5c6-a8987c0bafd5",  # invalid
                "contribution_answer": "foobar",
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data, {"error": "- Invalid contribution request. Try again."}
        )
        self.assertEqual(list(Pack.objects.all()), [])

    def test_propose_pack_no_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with no contributionrequest should not be accepted
        """
        logging.disable(logging.CRITICAL)
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        response = self.client.put(
            reverse("packs"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                }
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(Pack.objects.all()), [])
