from unittest.mock import patch

from core.models import Pack, PackStatus
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class EscalationAdminTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )
        self.client.force_login(self.user)
        self.pack = Pack.objects.create(
            pack_id="4830e258138fca961ab2151d9596755c",
            pack_key="87078ee421bad8bf44092ca72166b67ae5397e943452e4300ced9367b7f6a1a1",
            title="Escalated pack",
            author="Foo",
            status=PackStatus.IN_REVIEW.name,
        )

    def _escalate(self, button, **extra):
        with patch("core.admin.pack_admin.notify") as n:
            response = self.client.post(
                reverse("admin:core_pack_change", args=[self.pack.pk]),
                {
                    "pack_id": self.pack.pack_id,
                    "pack_key": self.pack.pack_key,
                    "title": self.pack.title,
                    "author": self.pack.author,
                    "status": "ESCALATED",
                    "animated_mode": "AUTO",
                    "animated": "on",
                    button: "1",
                    **extra,
                },
            )
        return response, n

    def test_escalate_notifies(self):
        response, n = self._escalate("_escalate")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Pack.objects.get(pk=self.pack.pk).status, PackStatus.ESCALATED.name
        )
        n.assert_called_once()

    def test_escalate_continue_notifies(self):
        response, n = self._escalate("_escalate_continue", _bulkreview_next="__last")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Pack.objects.get(pk=self.pack.pk).status, PackStatus.ESCALATED.name
        )
        n.assert_called_once()

    def test_reescalate_does_not_notify(self):
        self.pack.status = PackStatus.ESCALATED.name
        self.pack.save()
        response, n = self._escalate("_escalate")
        self.assertEqual(response.status_code, 302)
        n.assert_not_called()
