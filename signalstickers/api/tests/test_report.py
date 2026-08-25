from unittest.mock import patch

from core.models import (
    BotPreventionQuestion,
    Pack,
    PackStatus,
    Report,
    ReportStatus,
)
from core.notifications import NotificationPriority
from core.services import new_contribution_request
from core.utils import admin_url
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class ReportTestCase(TestCase):
    def setUp(self):
        question = BotPreventionQuestion(question="foo", answer="bar")
        question.save()

    def _create_pack(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")
        return Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            source="Source 1",
            nsfw=True,
            original=False,
            submitter_comments="",
            tags=["Foo1"],
            api_via="TestClient 1",
        )

    def _payload(self, contrib_req, pack_id="a" * 32, content=None):
        if content is None:
            content = "This pack contains inappropriate content."
        return {
            "contribution_id": contrib_req.id,
            "contribution_answer": contrib_req.question.answer,
            "pack_id": pack_id,
            "content": content,
        }

    def test_report_valid(self, mocked_getpacklib):
        """
        A valid report creates a Report and notifies the moderators
        """
        pack = self._create_pack(mocked_getpacklib)
        contrib_req = new_contribution_request("10.0.0.42")

        with patch("api.views.report_view.notify") as mocked_notify:
            response = self.client.put(
                reverse("api_v1:report"),
                self._payload(contrib_req),
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)

        self.assertEqual(Report.objects.count(), 1)
        report = Report.objects.first()
        self.assertEqual(report.pack, pack)
        self.assertEqual(report.status, ReportStatus.TO_PROCESS.name)
        self.assertEqual(report.content, "This pack contains inappropriate content.")

        mocked_notify.assert_called_once_with(
            "signalstickers-packs",
            "Pack reported",
            "Pack reported: Pack title",
            priority=NotificationPriority.HIGH,
            click_url=admin_url(),
        )

    def test_report_expired_contribution_request(self, mocked_getpacklib):
        """
        A report with an expired contribution request is rejected
        """
        self._create_pack(mocked_getpacklib)
        contrib_req = new_contribution_request("10.0.0.42")
        contrib_req.request_date = "2019-12-21 13:47Z"
        contrib_req.save()

        response = self.client.put(
            reverse("api_v1:report"),
            self._payload(contrib_req),
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data, {"error": "Invalid contribution request."})
        self.assertEqual(Report.objects.count(), 0)

    def test_report_unknown_pack(self, mocked_getpacklib):
        """
        A report for an unknown pack is rejected
        """
        self._create_pack(mocked_getpacklib)
        contrib_req = new_contribution_request("10.0.0.42")

        with patch("api.views.report_view.notify") as mocked_notify:
            response = self.client.put(
                reverse("api_v1:report"),
                self._payload(contrib_req, pack_id="b" * 32),
                content_type="application/json",
                REMOTE_ADDR="10.0.0.42",
            )

        self.assertEqual(status.HTTP_404_NOT_FOUND, response.status_code)
        self.assertEqual(response.data, {"error": "Unknown pack."})
        self.assertEqual(Report.objects.count(), 0)
        mocked_notify.assert_not_called()

    def test_report_invalid_payload(self, mocked_getpacklib):
        """
        A report with an invalid payload (content too short) is rejected
        """
        self._create_pack(mocked_getpacklib)
        contrib_req = new_contribution_request("10.0.0.42")

        response = self.client.put(
            reverse("api_v1:report"),
            self._payload(contrib_req, content="too short"),
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(response.data, {"error": "Invalid report."})
        self.assertEqual(Report.objects.count(), 0)
