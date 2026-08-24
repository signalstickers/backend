from unittest.mock import patch
from uuid import UUID

from core.models import ApiKey, Pack, PackStatus
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
@override_settings(AI_REVIEW_API_KEY="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
class InReviewPacksTestCase(TestCase):
    def setUp(self):
        self.api_key = ApiKey(
            key=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), name="test_client"
        )
        self.api_key.save()

    def test_get_inreview_packs(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.IN_REVIEW.name,
            source="reddit/r/test",
            submitter_comments="This is a great pack!",
            tags=["animals", "cute", "nature"],
        )

        mocked_getpacklib.return_value = TestPack(
            "Pack title 2", "Pack author 2", b"\x00"
        )
        Pack.objects.new(
            pack_id="c" * 32,
            pack_key="d" * 64,
            status=PackStatus.IN_REVIEW.name,
            source="",
            submitter_comments="",
            tags=[],
        )

        mocked_getpacklib.return_value = TestPack(
            "Pack title 3", "Pack author 3", b"\x00"
        )
        Pack.objects.new(
            pack_id="e" * 32,
            pack_key="f" * 64,
            status=PackStatus.ONLINE.name,
            source="online source",
            submitter_comments="online comments",
            tags=["online"],
        )

        mocked_getpacklib.return_value = TestPack(
            "Pack title 4", "Pack author 4", b"\x00"
        )
        Pack.objects.new(
            pack_id="g" * 32,
            pack_key="h" * 64,
            status=PackStatus.REFUSED.name,
        )

        mocked_getpacklib.return_value = TestPack(
            "Pack title 5", "Pack author 5", b"\x00"
        )
        Pack.objects.new(
            pack_id="i" * 32,
            pack_key="j" * 64,
            status=PackStatus.ESCALATED.name,
        )

        response = self.client.get(
            reverse("api_v1:packsinreview"),
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual(len(response.data), 2)

        pack_ids = [p["id"] for p in response.data]
        self.assertIn("a" * 32, pack_ids)
        self.assertIn("c" * 32, pack_ids)
        self.assertNotIn("e" * 32, pack_ids)
        self.assertNotIn("g" * 32, pack_ids)
        self.assertNotIn("i" * 32, pack_ids)

        for pack in response.data:
            self.assertIn("id", pack)
            self.assertIn("key", pack)
            self.assertIn("source", pack)
            self.assertIn("submitter_comments", pack)
            self.assertIn("tags", pack)
            self.assertEqual(len(pack), 5)

        pack1_data = next(p for p in response.data if p["id"] == "a" * 32)
        self.assertEqual(pack1_data["source"], "reddit/r/test")
        self.assertEqual(pack1_data["submitter_comments"], "This is a great pack!")
        self.assertEqual(pack1_data["tags"], ["animals", "cute", "nature"])

        pack2_data = next(p for p in response.data if p["id"] == "c" * 32)
        self.assertEqual(pack2_data["source"], "")
        self.assertEqual(pack2_data["submitter_comments"], "")
        self.assertEqual(pack2_data["tags"], [])

    def test_get_inreview_unauthorized_no_token(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.IN_REVIEW.name,
        )

        response = self.client.get(reverse("api_v1:packsinreview"))

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Unauthorized"}, response.data)

    def test_get_inreview_unauthorized_bad_token(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.IN_REVIEW.name,
        )

        response = self.client.get(
            reverse("api_v1:packsinreview"),
            HTTP_X_AUTH_TOKEN="cccccccc-cccc-cccc-cccc-cccccccccccc",
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Unauthorized"}, response.data)

    def test_get_inreview_empty(self, _):
        response = self.client.get(
            reverse("api_v1:packsinreview"),
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual([], response.data)
