from unittest.mock import patch
from uuid import UUID

from core.models import (
    ApiKey,
    BotPreventionQuestion,
    ContributionRequest,
    Pack,
    PackStatus,
)
from core.services import (
    check_api_key,
    clear_contribution_requests,
    new_contribution_request,
)
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status

from signalstickers.tests_common import TestPack


@patch("core.models.pack.get_pack_from_signal", autospec=True)
class ContributionTestCase(TestCase):
    def setUp(self):
        question = BotPreventionQuestion(question="foo", answer="bar")
        question.save()

    def test_get_expired_cr(self, _):
        cont_req_ok = new_contribution_request("127.0.0.1")
        cont_req_ok.save()

        cont_req_expired = new_contribution_request("127.0.0.1")
        cont_req_expired.request_date = "2019-12-21 13:47Z"
        cont_req_expired.save()

        self.assertEqual(ContributionRequest.objects.count(), 2)

        expired_crs = ContributionRequest.objects.expired()
        self.assertEqual(expired_crs.count(), 1)
        self.assertEqual(expired_crs.first(), cont_req_expired)

        clear_contribution_requests()
        self.assertEqual(expired_crs.count(), 0)
        self.assertEqual(ContributionRequest.objects.count(), 1)
        self.assertEqual(ContributionRequest.objects.first(), cont_req_ok)

    def test_contribution_request(self, _):
        """
        API response for contributionrequest is correct
        """
        # Check response
        response = self.client.post(reverse("api_v1:contributionrequest"))
        resp_contribution_id = response.data["contribution_id"]
        self.assertEqual(response.status_code, 200)
        self.assertTrue(isinstance(resp_contribution_id, UUID))
        self.assertEqual(response.data["contribution_question"], "foo")

        # Check ContributionRequest obj
        self.assertEqual(ContributionRequest.objects.count(), 1)
        contrib_req = ContributionRequest.objects.first()
        self.assertEqual(contrib_req.id, resp_contribution_id)
        self.assertEqual(contrib_req.client_ip, "127.0.0.1")
        self.assertEqual(contrib_req.question.question, "foo")

    def test_propose_pack(self, mocked_getpacklib):
        """
        Valid Pack request
        """

        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        contrib_req = new_contribution_request("10.0.0.42")

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "source.example.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)
        self.assertEqual(1, len(Pack.objects.all()))
        self.assertEqual(0, len(Pack.objects.onlines()))

        pack = Pack.objects.get()

        self.assertEqual(pack.status, PackStatus.IN_REVIEW.name)
        self.assertEqual(pack.pack_id, "a" * 32)
        self.assertEqual(pack.pack_key, "b" * 64)
        self.assertEqual(pack.title, "Pack title")
        self.assertEqual(pack.author, "Pack author")
        self.assertEqual(pack.id_cover, 42)
        self.assertEqual(pack.source, "source.example.com")
        self.assertEqual(pack.nsfw, True)
        self.assertEqual(pack.original, False)
        self.assertEqual(
            sorted([str(t) for t in pack.tags.all()]), sorted(["foo", "bar", "foobar"])
        )
        self.assertEqual(pack.submitter_comments, "Thanks")

    def test_propose_pack_editorschoice_ignored(self, mocked_getpacklib):
        """
        A submitter must not be able to set the "editorschoice" flag.
        """

        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        contrib_req = new_contribution_request("10.0.0.42")

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "source.example.com",
                    "tags": ["Foo"],
                    "nsfw": False,
                    "original": False,
                    "editorschoice": True,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)

        pack = Pack.objects.get()
        self.assertFalse(pack.editorschoice)

    def test_propose_pack_api_key(self, mocked_getpacklib):
        """
        Valid Pack request with API key
        """

        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        api_key = ApiKey(
            key=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), name="foo_client"
        )
        api_key.save()

        response = self.client.put(  # nosec
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "source.example.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                }
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
            HTTP_X_AUTH_TOKEN="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )
        self.assertEqual(status.HTTP_401_UNAUTHORIZED, response.status_code)
        self.assertEqual({"error": "Bad API key"}, response.data)

        self.assertEqual(0, len(Pack.objects.all()))

    def test_propose_pack_api_key_bad_key(self, mocked_getpacklib):
        """
        Valid Pack request
        """

        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        api_key = ApiKey(
            key=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), name="foo_client"
        )
        api_key.save()

        response = self.client.put(  # nosec
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "source.example.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                }
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
            HTTP_X_AUTH_TOKEN="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        self.assertEqual(status.HTTP_200_OK, response.status_code)
        self.assertEqual({"success": True}, response.data)

        self.assertEqual(1, len(Pack.objects.all()))
        self.assertEqual(0, len(Pack.objects.onlines()))

        pack = Pack.objects.get()

        self.assertEqual(pack.status, PackStatus.IN_REVIEW.name)
        self.assertEqual(pack.pack_id, "a" * 32)
        self.assertEqual(pack.pack_key, "b" * 64)
        self.assertEqual(pack.title, "Pack title")
        self.assertEqual(pack.author, "Pack author")
        self.assertEqual(pack.id_cover, 42)
        self.assertEqual(pack.source, "source.example.com (via foo_client)")
        self.assertEqual(pack.nsfw, True)
        self.assertEqual(pack.original, False)
        self.assertEqual(
            sorted([str(t) for t in pack.tags.all()]), sorted(["foo", "bar", "foobar"])
        )

    def test_propose_pack_duplicate(self, mocked_getpacklib):
        """
        Propose a pack already in DB
        """

        mocked_getpacklib.return_value = TestPack("Pack title", "Pack author", b"\x00")

        # Pack already in DB
        Pack.objects.new(
            pack_id="a" * 32,
            pack_key="b" * 64,
            status=PackStatus.ONLINE.name,
            source="Source 1",
            nsfw=True,
            original=False,
            submitter_comments="Not visible in the API1",
            tags=["Foo1", "BAR1", "FooBar1"],
            api_via="TestClient 1",
        )
        self.assertEqual(1, len(Pack.objects.all()))  # Just to be sure

        # Invalid contribution (duplicate pack)
        contrib_req = new_contribution_request("10.0.0.42")
        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "",
                    "tags": [],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(status.HTTP_400_BAD_REQUEST, response.status_code)
        self.assertEqual(
            {
                "error": "This pack already exists, or has already been proposed (and is waiting for its approval)."
            },
            response.data,
        )
        self.assertEqual(1, len(Pack.objects.all()))

    def test_propose_pack_invalid_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with invalid contributionrequest should not be
        accepted
        """
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": "11111111-2222-3333-4444-555555555555",  # invalid
                "contribution_answer": "foobar",
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"error": "Security verification failed, reload and try again"},
        )
        self.assertEqual(list(Pack.objects.all()), [])

    def test_propose_pack_expired_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with expired contributionrequest should not be
        accepted
        """
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        contrib_req = new_contribution_request("127.0.0.1")
        contrib_req.request_date = "2019-12-21 13:47Z"
        contrib_req.save()

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {
                "error": (
                    "Security verification failed, reload and try again."
                    " Reason: you took too long"
                )
            },
        )
        self.assertEqual(list(Pack.objects.all()), [])

    def test_propose_pack_wrong_answer(self, mocked_getpacklib):
        """
        Packs requests with incorrect response to BotPreventionQuestion
        """
        mocked_getpacklib.return_value = TestPack("foo", "bar", b"\x00")

        contrib_req = new_contribution_request("127.0.0.1")
        contrib_req.save()

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": "WRONG ANSWER",
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {"error": "Wrong answer"})
        self.assertEqual(list(Pack.objects.all()), [])

    def test_propose_pack_bad_ip_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with a ContributionRequest assigned to another IP
        """
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        contrib_req = new_contribution_request("10.0.13.37")

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                },
                "contribution_id": contrib_req.id,
                "contribution_answer": contrib_req.question.answer,
                "submitter_comments": "Thanks",
            },
            content_type="application/json",
            REMOTE_ADDR="10.0.0.42",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"error": "Security verification failed, reload and try again"},
        )
        self.assertEqual(list(Pack.objects.all()), [])

    def test_propose_pack_no_contributionrequest(self, mocked_getpacklib):
        """
        Packs requests with no contributionrequest should not be accepted
        """
        mocked_getpacklib.return_value = TestPack(
            "Pack title 1", "Pack author 1", b"\x00"
        )

        response = self.client.put(
            reverse("api_v1:contribute"),
            {
                "pack": {
                    "pack_id": "a" * 32,
                    "pack_key": "b" * 64,
                    "source": "signalstickers.com",
                    "tags": ["Foo", "Bar", "Foobar"],
                    "nsfw": True,
                    "original": False,
                }
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(list(Pack.objects.all()), [])

    def test_check_api_key(self, _):
        api_key_1 = ApiKey(
            key=UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), name="foo_client"
        )
        api_key_1.save()
        api_key_2 = ApiKey(
            key=UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), name="bar_client"
        )
        api_key_2.save()

        self.assertEqual(
            check_api_key(key="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), api_key_1
        )
        self.assertEqual(
            check_api_key(key="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"), api_key_2
        )

        self.assertFalse(check_api_key("cccccccc-cccc-cccc-cccc-cccccccccccc"))


# pylint: disable=no-member
class BotPreventionQuestionTestCase(TestCase):
    def test_answer_regex_validation(self):
        # The BotPreventionQuestion's answer should match the regex ^[a-zA-Z0-9]+$, a ValidationError is raised if not.
        with self.assertRaises(ValidationError):
            BotPreventionQuestion.answer.field.run_validators(value="foo+bar")
