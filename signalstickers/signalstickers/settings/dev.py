from .common import *

SECRET_KEY = "dev_secret_key"

DEBUG = True

CORS_ALLOW_ALL_ORIGINS = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

INTERNAL_IPS = ["127.0.0.1"]


DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}
