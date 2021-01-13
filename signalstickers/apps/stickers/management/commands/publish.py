import json
import logging
from hashlib import sha1

from apps.stickers.models import Pack
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db.utils import IntegrityError
from github import Github

logger = logging.getLogger("main")


def _serialize_pack(pack):
    """
    Serialize a pack in the right format for publishing
    """
    meta = {
        "id": pack.pack_id,
        "key": pack.pack_key,
        "source": pack.source,
        "tags": [tag.name for tag in pack.tags.all()],
        "nsfw": pack.nsfw,
        "animated": pack.animated,
        "original": pack.original,
    }

    pack_repr = {
        "meta": {k: v for k, v in meta.items() if v},
        "manifest": {
            "title": pack.title,
            "author": pack.author,
            "cover": {"id": 0, "emoji": ""},
        },
    }
    return pack_repr


class Command(BaseCommand):
    help = "Serialize all packs and publish them on Github"

    def handle(self, *args, **options):

        pack_list = []

        for pack in Pack.objects.onlines():
            pack_list.append(_serialize_pack(pack))

        packs_repr = json.dumps(pack_list)

        gh_client = Github(settings.GITHUB_CONF["bot_token"])
        repo = gh_client.get_repo(settings.GITHUB_CONF["publish_repo_id"])

        # Get previous content
        contents = repo.get_contents(
            settings.GITHUB_CONF["outfile"],
            ref=settings.GITHUB_CONF["publish_repo_branch"],
        )

        # Compute new content SHA1
        new_content_sha = sha1(
            f"blob {len(packs_repr)}\0{packs_repr}".encode()
        ).hexdigest()

        if new_content_sha == contents.sha:
            logger.info("Already up to date")
            return False

        # Update
        ret = repo.update_file(
            contents.path,
            "Update stickers",
            packs_repr,
            contents.sha,
            branch=settings.GITHUB_CONF["publish_repo_branch"],
        )

        logger.info("Update done in commit %s", ret["commit"].sha)
