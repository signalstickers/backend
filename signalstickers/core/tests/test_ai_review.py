from unittest.mock import patch

from core.models import AIReview, AIReviewStatus, Pack, PackStatus
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class AIReviewTestCase(TestCase):
    def _create_pack(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("Test Pack", "Test Author", b"\x00")
        return Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
        )

    def test_creation_defaults(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview.objects.create(pack=pack)
        self.assertEqual(review.pack, pack)
        self.assertEqual(review.status, AIReviewStatus.REFUSE.name)
        self.assertEqual(review.review_comment, "")
        self.assertFalse(review.nsfw)
        self.assertEqual(review.confidence, 0.0)
        self.assertTrue(review.alert)
        self.assertEqual(str(review), f"AI review for {pack.title}")

    def test_creation_with_values(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview.objects.create(
            pack=pack,
            status=AIReviewStatus.REFUSE.name,
            review_comment="Bad content",
            nsfw=True,
            confidence=0.85,
            alert=True,
        )
        self.assertEqual(review.status, AIReviewStatus.REFUSE.name)
        self.assertEqual(review.review_comment, "Bad content")
        self.assertTrue(review.nsfw)
        self.assertEqual(review.confidence, 0.85)
        self.assertTrue(review.alert)

    def test_one_to_one_relationship(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        AIReview.objects.create(pack=pack)
        self.assertEqual(pack.ai_review.pack, pack)

    def test_confidence_valid_boundary_zero(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview.objects.create(pack=pack, confidence=0.0)
        review.full_clean()
        self.assertEqual(review.confidence, 0.0)

    def test_confidence_valid_boundary_one(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview.objects.create(pack=pack, confidence=1.0)
        review.full_clean()
        self.assertEqual(review.confidence, 1.0)

    def test_confidence_invalid_negative(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview(pack=pack, confidence=-0.1)
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_confidence_invalid_above_one(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review = AIReview(pack=pack, confidence=1.1)
        with self.assertRaises(ValidationError):
            review.full_clean()

    def test_unique_pack_constraint(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        AIReview.objects.create(pack=pack)
        with self.assertRaises(IntegrityError):
            AIReview.objects.create(pack=pack)

    def test_upsert_pattern(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        review, created = AIReview.objects.update_or_create(
            pack=pack,
            defaults={
                "status": AIReviewStatus.ACCEPT.name,
                "confidence": 0.9,
            },
        )
        self.assertTrue(created)
        self.assertEqual(review.confidence, 0.9)

        review, created = AIReview.objects.update_or_create(
            pack=pack,
            defaults={
                "status": AIReviewStatus.REFUSE.name,
                "confidence": 0.5,
            },
        )
        self.assertFalse(created)
        self.assertEqual(review.confidence, 0.5)
        self.assertEqual(review.status, AIReviewStatus.REFUSE.name)

    def test_cascade_delete(self, mocked_getpacklib):
        pack = self._create_pack(mocked_getpacklib)
        AIReview.objects.create(pack=pack)
        self.assertEqual(AIReview.objects.count(), 1)
        pack.delete()
        self.assertEqual(AIReview.objects.count(), 0)
