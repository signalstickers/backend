from http import HTTPStatus
import logging
from unittest.mock import patch

from core.models import Pack, PackStatus, SiteStat
from core.utils import get_current_ym_date, get_last_month_ym_date
from django.test import TestCase
from django.urls import reverse

from signalstickers.tests_common import TestPack

logging.disable(logging.CRITICAL)


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class PingTestCase(TestCase):
    def test_ping_home(self, _):

        self.assertEqual(SiteStat.objects.count(), 0)

        response = self.client.post(
            reverse("api_v2:send_analytics"),
            "target=home",
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(b"", response.content)

        self.assertEqual(SiteStat.objects.count(), 1)

        site_stat = SiteStat.objects.first()
        self.assertEqual(site_stat.month, get_current_ym_date())
        self.assertEqual(site_stat.visits, 1)

    def test_ping_pack_stats_already_exist(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        pack = Pack.objects.new(
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
        pack.stats = {get_last_month_ym_date(): 12, get_current_ym_date(): 13}
        pack.save()

        response = self.client.post(
            reverse("api_v2:send_analytics"),
            f"target={'a' * 32}",
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(b"", response.content)

        pack.refresh_from_db()

        self.assertEqual(
            pack.stats, {get_last_month_ym_date(): 12, get_current_ym_date(): 14}
        )

    def test_ping_pack_stats_no_stats(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        pack = Pack.objects.new(
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
        pack.save()

        response = self.client.post(
            reverse("api_v2:send_analytics"),
            f"target={'a' * 32}",
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(HTTPStatus.NO_CONTENT, response.status_code)
        self.assertEqual(b"", response.content)

        pack.refresh_from_db()

        self.assertEqual(pack.stats, {get_current_ym_date(): 1})

    def test_ping_pack_invalid(self, mocked_getpacklib):
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )
        pack = Pack.objects.new(
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
        pack.stats = {get_last_month_ym_date(): 12, get_current_ym_date(): 13}
        pack.save()

        response = self.client.post(
            reverse("api_v2:send_analytics"),
            f"target={'d' * 32}",
            content_type="application/x-www-form-urlencoded",
        )
        self.assertEqual(HTTPStatus.BAD_REQUEST, response.status_code)
        self.assertEqual({"detail": "Unknown pack"}, response.json())

        pack.refresh_from_db()

        self.assertEqual(
            pack.stats, {get_last_month_ym_date(): 12, get_current_ym_date(): 13}
        )

        response = self.client.post(
            reverse("api_v2:send_analytics"),
            f"target={'a' * 33}",  # Too long (max=32)
            content_type="application/x-www-form-urlencoded",
        )

        self.assertEqual(
            HTTPStatus.UNPROCESSABLE_ENTITY,
            response.status_code,
        )
        self.assertEqual(
            {
                "detail": [
                    {
                        "ctx": {"max_length": 32},
                        "loc": ["form", "data", "target", "constrained-str"],
                        "msg": "String should have at most 32 characters",
                        "type": "string_too_long",
                    },
                    {
                        "ctx": {"expected": "'home'"},
                        "loc": ["form", "data", "target", "literal['home']"],
                        "msg": "Input should be 'home'",
                        "type": "literal_error",
                    },
                ]
            },
            response.json(),
        )

        pack.refresh_from_db()

        self.assertEqual(
            pack.stats, {get_last_month_ym_date(): 12, get_current_ym_date(): 13}
        )
