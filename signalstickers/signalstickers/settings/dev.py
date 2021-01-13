import os

from .common import *

SECRET_KEY = "dev_secret_key"

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True


ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INTERNAL_IPS = ["127.0.0.1"]

ADMIN_URL = "admin/"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "normal": {"format": "%(asctime)s %(levelname)s %(module)s  %(message)s"}
    },
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "normal"}},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO"},
        "": {"handlers": ["console"], "level": "INFO"},
    },
}


GITHUB_CONF = {
    "bot_token": os.environ.get("GHTOKEN"),
    "publish_repo_id": "signalstickers/stickers-data",
    "publish_repo_branch": "master",
    "outfile": "all_stickers.json",
}

# Obtained from https://developer.twitter.com/
TWITTER_CONF = {
    "consumer_key": "foo",
    "consumer_secret": "bar",
    "access_token": "ga",
    "access_token_secret": "bu",
}
