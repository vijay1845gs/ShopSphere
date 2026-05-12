"""
Development settings — reads all values from .env file.
"""

from decouple import config
from .base import *  # noqa
from config.logging_config import get_logging_config

SECRET_KEY = config("SECRET_KEY", default="django-insecure-dev-only-key-change-in-production")

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Use Django's in-memory cache locally unless Redis is explicitly enabled.
# This keeps the development server usable without a local Redis service.
if not config("USE_REDIS_CACHE", default=False, cast=bool):
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "shopsphere-dev-cache",
            "TIMEOUT": config("CACHE_TTL", default=900, cast=int),
        }
    }

# PostgreSQL via Supabase
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": "require",  # Supabase requires SSL
        },
    }
}

# Development logging
LOGGING = get_logging_config(env="development")

# Site URL for development
SITE_URL = config("SITE_URL", default="http://localhost:8000")
