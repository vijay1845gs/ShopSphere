"""
Professional logging configuration for ShopSphere.
Provides structured logging with separate files for different concerns.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)


def get_logging_config(env: str = "development") -> dict:
    """
    Returns logging configuration with multiple handlers.

    Files created:
    - app.log: General application logs
    - error.log: Error-level logs only
    - security.log: Authentication and security events
    - celery.log: Task execution logs
    """

    # Safe formatters
    formatters = {
        "standard": {
            "format": "[{asctime}] {levelname} {name} - {message}",
            "style": "{",
        },
        "detailed": {
            "format": "[{asctime}] {levelname} {name}:{lineno} - {message}",
            "style": "{",
        },
    }

    # Handlers
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
        },

        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "app.log"),
            "formatter": "standard",
            "level": "INFO",
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
        },

        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "error.log"),
            "formatter": "detailed",
            "level": "ERROR",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
        },

        "security_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "security.log"),
            "formatter": "standard",
            "level": "INFO",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 10,
        },

        "celery_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOGS_DIR / "celery.log"),
            "formatter": "detailed",
            "level": "INFO",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
        },
    }

    # Environment-specific console level
    if env == "development":
        handlers["console"]["level"] = "DEBUG"
    else:
        handlers["console"]["level"] = "INFO"

    # Loggers
    loggers = {
        "django": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },

        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },

        # Authentication logger
        "shopsphere.auth": {
            "handlers": ["console", "app_file", "security_file"],
            "level": "INFO",
            "propagate": False,
        },

        # Order logger
        "shopsphere.orders": {
            "handlers": ["console", "app_file"],
            "level": "INFO",
            "propagate": False,
        },

        # Security logger
        "shopsphere.security": {
            "handlers": ["console", "security_file"],
            "level": "INFO",
            "propagate": False,
        },

        # Celery logger
        "celery": {
            "handlers": ["console", "celery_file"],
            "level": "INFO",
            "propagate": False,
        },

        "celery.task": {
            "handlers": ["console", "celery_file"],
            "level": "INFO",
            "propagate": False,
        },
    }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "loggers": loggers,
        "root": {
            "handlers": ["console", "app_file", "error_file"],
            "level": "INFO",
        },
    }