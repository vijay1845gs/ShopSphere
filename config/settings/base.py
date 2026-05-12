"""
Base settings shared across all environments.
Never put secrets or environment-specific values here.
"""

from pathlib import Path
from django.contrib.messages import constants as messages
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "drf_spectacular",  # OpenAPI schema generation
]

LOCAL_APPS = [
    "products",
    "cart",
    "accounts",
    "orders",
    "wishlist",
    "reviews",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # serves static files efficiently
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "product_list"

MESSAGE_TAGS = {
    messages.DEBUG: "secondary",
    messages.INFO: "info",
    messages.SUCCESS: "success",
    messages.WARNING: "warning",
    messages.ERROR: "danger",
}

# --- Django REST Framework ---
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",  # Use drf-spectacular
}

# --- SimpleJWT ---
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# --- drf-spectacular OpenAPI Settings ---
SPECTACULAR_SETTINGS = {
    "TITLE": "ShopSphere API",
    "VERSION": "1.0.0",
    "DESCRIPTION": (
        "ShopSphere is a full-featured e-commerce platform API. "
        "Provides product listings, cart management, order processing, "
        "wishlists, and reviews with JWT authentication."
    ),
    "SERVE_INCLUDE_SCHEMA": False,  # hide raw schema endpoint from public
    "COMPONENT_SPLIT_REQUEST": True,  # separate request/response serializers
    "SECURITY": [{"Bearer": []}],  # default security scheme for all endpoints
    "SECURITY_SCHEMES": {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    },
    "TAGS": [
        {"name": "Products", "description": "Product listing and details"},
        {"name": "Cart", "description": "Shopping cart operations"},
        {"name": "Orders", "description": "Order placement and management"},
        {"name": "Wishlist", "description": "User wishlist management"},
        {"name": "Reviews", "description": "Product reviews and ratings"},
        {"name": "Authentication", "description": "JWT token obtain and refresh"},
    ],
    "SORT_OPERATIONS": True,  # alphabetical tag and operation ordering
}

# --- Logging ---
from config.logging_config import get_logging_config

LOGGING = get_logging_config(env=config("ENV", default="development"))

# Site URL for absolute URLs in emails
SITE_URL = config("SITE_URL", default="http://localhost:8000")

# --- Caching (Redis) ---
# Production-grade caching for querysets and rendered fragments
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379, cast=int)}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": config("REDIS_PASSWORD", default=""),
            "CONNECTION_POOL_KWARGS": {
                "max_connections": 50,  # reasonable connection pool limit
                "retry_on_timeout": True,
            },
        },
        "KEY_PREFIX": "shopsphere",  # namespacing for multi-app environments
        "TIMEOUT": config("CACHE_TTL", default=900, cast=int),  # 15 minutes default
    }
}

# Cache key versioning for safe invalidation
CACHE_VERSION = 1

# --- Celery Async Tasks ---
# Redis broker URL is configured in celery.py using environment variables
# These defaults mirror the cache configuration
CELERY_TASK_ALWAYS_EGRESS = config("CELERY_TASK_ALWAYS_EGRESS", default=True, cast=bool)
CELERY_TASK_EAGER_PROPAGATES = config("CELERY_TASK_EAGER_PROPAGATES", default=True, cast=bool)
CELERY_TASK_IGNORE_RESULT = config("CELERY_TASK_IGNORE_RESULT", default=False, cast=bool)
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
