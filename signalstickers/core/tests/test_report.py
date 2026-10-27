from core.models import Pack, PackStatus, Report, ReportStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class ReportAdminTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        self.client.force_login(self.user)
        self.pack = Pack.objects.create(
            pack_id="4830e258138fca961ab2151d9596755c",
            pack_key="87078ee421bad8bf44092ca72166b67ae5397e943452e4300ced9367b7f6a1a1",
            title="Reported pack",
            author="Foo",
            status=PackStatus.ONLINE.name,
        )
        self.report = Report.objects.create(
            pack=self.pack,
            content="This pack is inappropriate.",
            status=ReportStatus.TO_PROCESS.name,
        )

    def _post(self, button):
        return self.client.post(
            reverse("admin:core_report_change", args=[self.report.pk]),
            {button: "1"},
        )

    def test_agree(self):
        response = self._post("_agree")
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.AGREED.name)

    def test_disagree(self):
        response = self._post("_disagree")
        self.assertEqual(response.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.DISAGREED.name)

    def test_agree_redirects_to_changelist(self):
        response = self._post("_agree")
        self.assertEqual(
            response.url,
            reverse("admin:core_report_changelist"),
        )
