from http import HTTPStatus
from unittest.mock import patch

from core.models import AIReview, AIReviewStatus, Pack, PackStatus
from django.test import TestCase, override_settings
from django.urls import reverse

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
@override_settings(AI_REVIEW_API_KEY="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
class AIReviewAPITestCase(TestCase):
    token = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    def _create_pack(
        self, mocked_getpacklib, title, pack_id, pack_key, status, **kwargs
    ):
        mocked_getpacklib.return_value = TestPack(title, "Test author", b"\x00")
        return Pack.objects.new(
            pack_id=pack_id,
            pack_key=pack_key,
            status=status,
            **kwargs,
        )

    # ---------- GET /v2/admin/toreview/ ----------

    def test_get_in_review_packs(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
            source="reddit/r/test",
            submitter_comments="This is a great pack!",
            tags=["animals", "cute", "nature"],
        )
        self._create_pack(
            mocked_getpacklib,
            "Pack title 2",
            "c" * 32,
            "d" * 64,
            PackStatus.IN_REVIEW.name,
        )
        # Packs with other statuses must not be returned
        self._create_pack(
            mocked_getpacklib,
            "Pack title 3",
            "e" * 32,
            "f" * 64,
            PackStatus.ONLINE.name,
        )
        self._create_pack(
            mocked_getpacklib,
            "Pack title 4",
            "g" * 32,
            "h" * 64,
            PackStatus.REFUSED.name,
        )
        self._create_pack(
            mocked_getpacklib,
            "Pack title 5",
            "i" * 32,
            "j" * 64,
            PackStatus.ESCALATED.name,
        )

        response = self.client.get(
            reverse("api_v2:get_in_review_packs"),
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(
            response.json(),
            [
                {
                    "id": "a" * 32,
                    "key": "b" * 64,
                    "source": "reddit/r/test",
                    "submitter_comments": "This is a great pack!",
                    "tags": ["animals", "cute", "nature"],
                },
                {
                    "id": "c" * 32,
                    "key": "d" * 64,
                    "source": "",
                    "submitter_comments": "",
                    "tags": [],
                },
            ],
        )

    def test_get_in_review_packs_only_noaireview(self, mocked_getpacklib):
        pack1 = self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )
        self._create_pack(
            mocked_getpacklib,
            "Pack title 2",
            "c" * 32,
            "d" * 64,
            PackStatus.IN_REVIEW.name,
        )
        AIReview.objects.create(
            pack=pack1,
            status=AIReviewStatus.ACCEPT.name,
            confidence=0.9,
        )

        # Without the param: both packs are returned
        response = self.client.get(
            reverse("api_v2:get_in_review_packs"),
            HTTP_X_AUTH_TOKEN=self.token,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual([p["id"] for p in response.json()], ["a" * 32, "c" * 32])

        # only_noaireview=true: only the pack without an AI review
        response = self.client.get(
            reverse("api_v2:get_in_review_packs"),
            {"only_noaireview": "true"},
            HTTP_X_AUTH_TOKEN=self.token,
        )
        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual([p["id"] for p in response.json()], ["c" * 32])

    def test_get_in_review_packs_unauthorized_no_token(self, _):
        response = self.client.get(reverse("api_v2:get_in_review_packs"))

        self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unauthorized",
                        "loc": ["header", "X-Auth-Token"],
                        "msg": "Unauthorized",
                    }
                ]
            },
        )

    def test_get_in_review_packs_unauthorized_bad_token(self, _):
        response = self.client.get(
            reverse("api_v2:get_in_review_packs"),
            HTTP_X_AUTH_TOKEN="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )

        self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unauthorized",
                        "loc": ["header", "X-Auth-Token"],
                        "msg": "Unauthorized",
                    }
                ]
            },
        )

    @override_settings(AI_REVIEW_API_KEY=None)
    def test_get_in_review_packs_unauthorized_key_unset(self, _):
        """
        With AI_REVIEW_API_KEY unset (None), auth must fail closed:
        a missing token is a 401, not a bypass.
        """
        response = self.client.get(reverse("api_v2:get_in_review_packs"))

        self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unauthorized",
                        "loc": ["header", "X-Auth-Token"],
                        "msg": "Unauthorized",
                    }
                ]
            },
        )

    def test_get_in_review_packs_empty(self, _):
        response = self.client.get(
            reverse("api_v2:get_in_review_packs"),
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.OK, response.status_code)
        self.assertEqual(response.json(), [])

    # ---------- PUT /v2/admin/aireview/ ----------

    def test_ai_review_creation(self, mocked_getpacklib):
        pack = self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "ACCEPT",
                "review_comment": "Looks good",
                "nsfw": False,
                "tags_match": True,
                "confidence": 0.95,
                "alert": False,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(b"", response.content)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.status, AIReviewStatus.ACCEPT.name)
        self.assertEqual(review.review_comment, "Looks good")
        self.assertFalse(review.nsfw)
        self.assertTrue(review.tags_match)
        self.assertEqual(review.confidence, 0.95)
        self.assertFalse(review.alert)

    def test_ai_review_upsert(self, mocked_getpacklib):
        pack = self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )
        AIReview.objects.create(
            pack=pack,
            status=AIReviewStatus.ACCEPT.name,
            confidence=0.9,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "REFUSE",
                "confidence": 0.5,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(AIReview.objects.count(), 1)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.status, AIReviewStatus.REFUSE.name)
        self.assertEqual(review.confidence, 0.5)

    def test_ai_review_unauthorized_no_token(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
        )

        self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unauthorized",
                        "loc": ["header", "X-Auth-Token"],
                        "msg": "Unauthorized",
                    }
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_unauthorized_bad_token(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )

        self.assertEqual(HTTPStatus.UNAUTHORIZED, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unauthorized",
                        "loc": ["header", "X-Auth-Token"],
                        "msg": "Unauthorized",
                    }
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_unknown_pack(self, _):
        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                # Unknown but valid pack id (32 hex chars)
                "pack_id": "f" * 32,
                "status": "ACCEPT",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "unknown_pack",
                        "loc": ["body", "data", "pack_id"],
                        "msg": "Unknown pack",
                    }
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_missing_required_fields(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": "a" * 32,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.UNPROCESSABLE_ENTITY, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "data", "status"],
                        "msg": "Field required",
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "data", "confidence"],
                        "msg": "Field required",
                    },
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_invalid_status(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "MAYBE",
                "confidence": 0.95,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.UNPROCESSABLE_ENTITY, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "enum",
                        "loc": ["body", "data", "status"],
                        "msg": "Input should be 'Accept' or 'Refuse'",
                        "ctx": {"expected": "'Accept' or 'Refuse'"},
                    }
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_confidence_out_of_range(self, mocked_getpacklib):
        self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": "a" * 32,
                "status": "ACCEPT",
                "confidence": 1.5,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.UNPROCESSABLE_ENTITY, response.status_code)
        self.assertEqual(
            response.json(),
            {
                "detail": [
                    {
                        "type": "less_than_equal",
                        "loc": ["body", "data", "confidence"],
                        "msg": "Input should be less than or equal to 1",
                        "ctx": {"le": 1.0},
                    }
                ]
            },
        )
        self.assertEqual(AIReview.objects.count(), 0)

    def test_ai_review_optional_fields_defaults(self, mocked_getpacklib):
        pack = self._create_pack(
            mocked_getpacklib,
            "Pack title 1",
            "a" * 32,
            "b" * 64,
            PackStatus.IN_REVIEW.name,
        )

        response = self.client.put(
            reverse("api_v2:update_ai_review"),
            {
                "pack_id": pack.pack_id,
                "status": "ACCEPT",
                "confidence": 0.8,
            },
            content_type="application/json",
            HTTP_X_AUTH_TOKEN=self.token,
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)

        review = AIReview.objects.get(pack=pack)
        self.assertEqual(review.review_comment, "")
        self.assertFalse(review.nsfw)
        self.assertFalse(review.tags_match)
        self.assertFalse(review.alert)
