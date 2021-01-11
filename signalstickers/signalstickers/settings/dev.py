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


# Use this for Dummy Cache
# CACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

# Use this for Dockerized Memcached

CACHE_HOST = "127.0.0.1"
CACHE_PORT = 11211
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        "LOCATION": f"{CACHE_HOST}:{CACHE_PORT}",
    }
}
