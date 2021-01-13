import json
import logging
from hashlib import sha1

from django.conf import settings
from github import Github
from libs.twitter_bot import tweet_pack

from apps.stickers.models import Pack

logger = logging.getLogger("main")


def tweet_command():
    """
    Tweet packs tagged as 'not tweeted'
    """

    not_tweeted_packs = Pack.objects.not_twitteds()

    nb_packs_twitted = 0
    errs = []

    for pack in not_tweeted_packs:
        try:
            logger.info("Start tweeting about %s", pack.pack_id)
            tweet_pack(pack)
            logger.info("Tweet about %s done", pack.pack_id)

            # Set pack as "tweeted"
            pack.tweeted = True
            pack.save()
            nb_packs_twitted += 1

        except Exception as e:
            mess = f"Error while tweeting {pack.pack_id}: {e}"
            logger.error(mess)
            errs.append(mess)

    return nb_packs_twitted, errs


def publish_command():
    """
    Serialize all packs and publish them on Github
    """

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

    print("hello bb from print")
    pack_list = []

    for pack in Pack.objects.onlines():
        pack_list.append(_serialize_pack(pack))

    packs_repr = json.dumps(pack_list)

    gh_client = Github(settings.GITHUB_CONF["bot_token"])
    repo = gh_client.get_repo(settings.GITHUB_CONF["publish_repo_id"])

    # Get previous content
    contents = repo.get_contents(
        settings.GITHUB_CONF["outfile"], ref=settings.GITHUB_CONF["publish_repo_branch"]
    )

    # Compute new content SHA1
    new_content_sha = sha1(f"blob {len(packs_repr)}\0{packs_repr}".encode()).hexdigest()

    if new_content_sha == contents.sha:
        mess = "Already up to date"
        logger.info(mess)

        return False, mess

    # Update
    ret = repo.update_file(
        contents.path,
        "Update stickers",
        packs_repr,
        contents.sha,
        branch=settings.GITHUB_CONF["publish_repo_branch"],
    )

    mess = f"Update done in commit {ret['commit'].sha}. Total packs: {len(pack_list)}"
    logger.info(mess)

    return True, mess
