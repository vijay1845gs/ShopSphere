"""
Production settings — deployed server only.
All secrets come from environment variables. Never hardcode here.
"""

from decouple import config, Csv
from .base import *  # noqa

SECRET_KEY = config("SECRET_KEY")

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# --- PostgreSQL ---
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("DB_NAME"),
        "USER": config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        "HOST": config("DB_HOST", default="localhost"),
        "PORT": config("DB_PORT", default="5432"),
        "CONN_MAX_AGE": 60,  # persistent connections — reduces overhead per request
    }
}

# --- Security Hardening ---
SECURE_HSTS_SECONDS = 31536000          # force HTTPS for 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = True              # redirect all HTTP → HTTPS
SESSION_COOKIE_SECURE = True            # cookies only over HTTPS
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# --- Email (configure per provider) ---
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="noreply@shopsphere.com")

# Admin email for alerts
ADMIN_EMAIL = config("ADMIN_EMAIL", default=DEFAULT_FROM_EMAIL)

# Site URL for absolute URLs in emails
SITE_URL = config("SITE_URL", default="https://shopsphere.com")

# --- Logging ---
# Use production logging config
LOGGING = get_logging_config(env="production")
