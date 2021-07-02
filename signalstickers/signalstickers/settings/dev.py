import os

from .common import *

SECRET_KEY = "dev_secret_key"

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True


ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INTERNAL_IPS = ["127.0.0.1"]

ADMIN_URL = "admin/"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "django",
        "USER": "django",
        "PASSWORD": "this_password_is_for_dev_only_NOT_FOR_PROD",
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}


if os.environ.get("GITHUB_WORKFLOW"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": "github_actions",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "HOST": "127.0.0.1",
            "PORT": "5432",
        }
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


# Obtained from https://developer.twitter.com/
TWITTER_CONF = {
    "consumer_key": "foo",
    "consumer_secret": "bar",
    "access_token": "ga",
    "access_token_secret": "bu",
}

HEADER_IP = "REMOTE_ADDR"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_FROM = '"Signalstickers" <Signalstickers@example.com>'
