from unittest.mock import patch
from uuid import UUID

from core.models import AIReview, AIReviewStatus, ApiKey, Pack, PackStatus
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
@override_settings(AI_REVIEW_API_KEY="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
class AIReviewViewTestCase(TestCase):
    def setUp(self):
        self.api_key = ApiKey(
            key=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), name="ai_client"
        )
        self.api_key.save()

    def _create_pack(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("Test Pack", "Test Author", b"\x00")
        return Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
        )

    def test_successful_review_creation(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "ACCEPT",
                "review_comment": "Looks good",
                "nsfw": False,
                "confidence": 0.95,
                "alert": False,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.status, AIReviewStatus.ACCEPT.name)
        self.assertEqual(review.review_comment, "Looks good")
        self.assertFalse(review.nsfw)
        self.assertEqual(review.confidence, 0.95)
        self.assertFalse(review.alert)

    def test_successful_review_upsert(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)

        AIReview.objects.create(
            pack=pack,
            status=AIReviewStatus.ACCEPT.name,
            confidence=0.9,
        )

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "REFUSE",
                "confidence": 0.5,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)
        self.assertEqual(AIReview.objects.count(), 1)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.status, AIReviewStatus.REFUSE.name)
        self.assertEqual(review.confidence, 0.5)

    def test_unauthorized_no_token(self, mocked_getpacklib):
        self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Bad API key"}, response.data)

    def test_unauthorized_bad_token(self, mocked_getpacklib):
        self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )

        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Bad API key"}, response.data)

    def test_unknown_pack(self, _):
        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": "z" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual({"error": "Unknown pack."}, response.data)

    def test_invalid_payload_missing_required(self, mocked_getpacklib):
        self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": "a" * 32,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_invalid_pack_id_length(self, mocked_getpacklib):
        self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": "a" * 10,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)

    def test_optional_fields_defaults(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)

        response = self.client.put(
            reverse("api_v1:ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "ACCEPT",
                "confidence": 0.8,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.review_comment, "")
        self.assertFalse(review.nsfw)
        self.assertFalse(review.alert)
