from unittest.mock import patch

from core.notifications import NotificationPriority
from django.contrib.auth import get_user_model
from django.test import TestCase


class AdminLoginTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser(
            username="admin", email="admin@example.com", password="pass"
        )

    def test_successful_login_notifies(self):
        with patch("core.adminsite.notify") as n:
            response = self.client.post(
                "/admin/login/",
                {"username": "admin", "password": "pass"},
            )
        self.assertEqual(response.status_code, 302)
        n.assert_called_once()
        args, kwargs = n.call_args
        self.assertEqual(args[0], "signalstickers-admin")
        self.assertEqual(args[1], "Admin login")
        self.assertEqual(args[2], "Admin 'admin' logged in from 127.0.0.1")
        self.assertEqual(kwargs["priority"], NotificationPriority.DEFAULT)
        self.assertEqual(kwargs["tags"], ["lock"])

    def test_failed_login_does_not_notify(self):
        with patch("core.adminsite.notify") as n:
            response = self.client.post(
                "/admin/login/",
                {"username": "admin", "password": "wrong"},
            )
        self.assertEqual(response.status_code, 200)
        n.assert_not_called()

    def test_get_login_does_not_notify(self):
        with patch("core.adminsite.notify") as n:
            response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 200)
        n.assert_not_called()
