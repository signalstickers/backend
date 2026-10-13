from unittest.mock import MagicMock, patch

from core.notifications import Notification, NotificationPriority, _send, notify
from django.test import TestCase, override_settings


class NotifyTestCase(TestCase):
    @override_settings(
        NTFY_SERVER_URL="https://ntfy.example.com", NTFY_AUTH_TOKEN="tok"
    )
    def test_notify_dispatches(self):
        # Run the executor task inline so the assertion is deterministic
        # (notify() is otherwise fire-and-forget on a worker thread).
        with patch("core.notifications._send") as s, patch(
            "core.notifications._executor.submit", side_effect=lambda fn, *a: fn(*a)
        ):
            notify(
                "packs",
                "A title",
                "Hello",
                tags=["a"],
                priority=NotificationPriority.HIGH,
                click_url="https://example.com/admin/",
            )
            s.assert_called_once()
            n = s.call_args.args[0]
            self.assertEqual(n.topic, "packs")
            self.assertEqual(n.title, "A title")
            self.assertEqual(n.message, "Hello")
            self.assertEqual(n.tags, ["a"])
            self.assertEqual(n.priority, NotificationPriority.HIGH)

    @override_settings(NTFY_SERVER_URL="")
    def test_notify_noop_when_unconfigured(self):
        with patch("core.notifications._send") as s, patch(
            "core.notifications._executor.submit", side_effect=lambda fn, *a: fn(*a)
        ):
            notify("t", "A title", "m")
            s.assert_not_called()

    @override_settings(
        NTFY_SERVER_URL="https://ntfy.example.com", NTFY_AUTH_TOKEN="tok"
    )
    def test_send_success(self):
        resp = MagicMock()
        resp.is_success = True
        resp.status_code = 200
        resp.text = "OK"
        client = MagicMock()
        client.post.return_value = resp
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        with patch("core.notifications.httpx.Client", return_value=client):
            _send(
                Notification(
                    topic="packs",
                    title="A title",
                    message="Hello",
                    tags=["a", "b"],
                    priority=NotificationPriority.HIGH,
                    click_url="https://example.com/admin/",
                )
            )
        client.post.assert_called_once()
        args, kwargs = client.post.call_args
        self.assertEqual(args[0], "https://ntfy.example.com/packs")
        self.assertEqual(kwargs["content"], "Hello")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer tok")
        self.assertEqual(kwargs["headers"]["Priority"], "high")
        self.assertEqual(kwargs["headers"]["Tags"], "a,b")

    @override_settings(NTFY_SERVER_URL="https://ntfy.example.com", NTFY_AUTH_TOKEN="")
    def test_send_no_auth_header_without_token(self):
        resp = MagicMock()
        resp.is_success = True
        client = MagicMock()
        client.post.return_value = resp
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        with patch("core.notifications.httpx.Client", return_value=client):
            _send(
                Notification(
                    topic="t",
                    title="A title",
                    message="m",
                    click_url="https://example.com/admin/",
                )
            )
        args, kwargs = client.post.call_args
        self.assertNotIn("Authorization", kwargs["headers"])

    @override_settings(NTFY_SERVER_URL="https://ntfy.example.com")
    def test_send_http_error_is_swallowed(self):
        resp = MagicMock()
        resp.is_success = False
        resp.status_code = 500
        resp.text = "boom"
        client = MagicMock()
        client.post.return_value = resp
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        with patch("core.notifications.httpx.Client", return_value=client):
            _send(
                Notification(
                    topic="t",
                    title="A title",
                    message="m",
                    click_url="https://example.com/admin/",
                )
            )  # must not raise

    @override_settings(NTFY_SERVER_URL="https://ntfy.example.com")
    def test_send_swallows_errors(self):
        client = MagicMock()
        client.post.side_effect = Exception("network down")
        client.__enter__ = MagicMock(return_value=client)
        client.__exit__ = MagicMock(return_value=False)
        with patch("core.notifications.httpx.Client", return_value=client):
            _send(
                Notification(
                    topic="t",
                    title="A title",
                    message="m",
                    click_url="https://example.com/admin/",
                )
            )  # must not raise
