from http import HTTPStatus
from unittest.mock import patch

from core.models import BotPreventionQuestion, Pack, PackStatus, Report, ReportStatus
from core.notifications import NotificationPriority
from core.services import new_contribution_request
from core.utils import admin_url
from django.test import TestCase
from django.urls import reverse

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class ReportAPITestCase(TestCase):
    def setUp(self):
        question = BotPreventionQuestion(question="foo", answer="bar")
        question.save()

    def test_report_ok(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        contrib_req = new_contribution_request("10.0.0.42")

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

        with patch("api_v2.routes.packs.notify") as mocked_notify:
            response = self.client.post(
                reverse("api_v2:report"),
                {
                    "pack_id": "a" * 32,
                    "content": "foo" * 20,
                    "security_id": contrib_req.id,
                    "security_answer": contrib_req.question.answer,
                },
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )
        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(b"", response.content)

        report = Report.objects.get()

        self.assertEqual(report.pack.pack_id, "a" * 32)
        self.assertEqual(report.content, "foo" * 20)
        self.assertEqual(report.status, ReportStatus.TO_PROCESS.name)

        mocked_notify.assert_called_once_with(
            "signalstickers-packs",
            "Pack reported",
            "Pack reported: Pack title 1",
            priority=NotificationPriority.HIGH,
            click_url=admin_url(),
        )

    def test_report_pack_noexists(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        contrib_req = new_contribution_request("10.0.0.42")

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

        with patch("api_v2.routes.packs.notify") as mocked_notify:
            response = self.client.post(
                reverse("api_v2:report"),
                {
                    "pack_id": "b" * 32,
                    "content": "foo" * 20,
                    "security_id": contrib_req.id,
                    "security_answer": contrib_req.question.answer,
                },
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )
        self.assertEqual(HTTPStatus.NOT_FOUND, response.status_code)
        self.assertEqual(
            {
                "detail": [
                    {
                        "type": "unknown_pack",
                        "loc": ["body", "data", "pack_id"],
                        "msg": "Unknown pack",
                    }
                ]
            },
            response.json(),
        )

        self.assertEqual(0, len(Report.objects.all()))
        mocked_notify.assert_not_called()

    def test_report_pack_invalid_contributionrequest(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        contrib_req = new_contribution_request("10.0.0.42")

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

        with patch("api_v2.routes.packs.notify") as mocked_notify:
            response = self.client.post(
                reverse("api_v2:report"),
                {
                    "pack_id": "a" * 32,
                    "content": "foo" * 20,
                    "security_id": "00000000-0000-4000-a000-000000000000",  # invalid
                    "security_answer": contrib_req.question.answer,
                },
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )
        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "detail": [
                    {
                        "type": "security_verification_failed",
                        "loc": ["body", "data", "security_id"],
                        "msg": "Security verification failed, reload and try again",
                    }
                ]
            },
            response.json(),
        )

        self.assertEqual(0, len(Report.objects.all()))
        mocked_notify.assert_not_called()

    def test_report_pack_invalid_wrong_answer(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        contrib_req = new_contribution_request("10.0.0.42")

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

        with patch("api_v2.routes.packs.notify") as mocked_notify:
            response = self.client.post(
                reverse("api_v2:report"),
                {
                    "pack_id": "a" * 32,
                    "content": "foo" * 20,
                    "security_id": contrib_req.id,
                    "security_answer": "WRONG ANSWER",
                },
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )
        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "detail": [
                    {
                        "type": "wrong_answer",
                        "loc": ["body", "data", "security_answer"],
                        "msg": "Wrong answer",
                    }
                ]
            },
            response.json(),
        )

        self.assertEqual(0, len(Report.objects.all()))
        mocked_notify.assert_not_called()
