"""
Celery configuration for ShopSphere
====================================
Asynchronous task queue using Redis as message broker.
"""

import os
from celery import Celery
from decouple import config

# Set default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

# Create Celery app
app = Celery("shopsphere")

# Configuration from Django settings + environment overrides
app.conf.update(
    # Broker — Redis URL from env
    broker_url=config(
        "CELERY_BROKER_URL",
        default=f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379, cast=int)}/0",
    ),
    # Result backend — store task results in Redis
    result_backend=config(
        "CELERY_RESULT_BACKEND",
        default=f"redis://{config('REDIS_HOST', default='localhost')}:{config('REDIS_PORT', default=6379, cast=int)}/1",
    ),
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,
    # Task execution settings
    task_track_started=True,
    task_send_sent_event=True,
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    # Task result settings
    result_expires=86400,
    # Security
    worker_hijack_root_logger=False,
)

# Celery Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Hourly low stock alerts
    "low-stock-alert-hourly": {
        "task": "orders.tasks.send_low_stock_alert",
        "schedule": 3600.0,
    },
    # Daily analytics at midnight
    "daily-analytics": {
        "task": "orders.tasks.generate_daily_analytics",
        "schedule": 86400.0,
    },
    # Daily session cleanup
    "cleanup-expired-sessions": {
        "task": "orders.tasks.cleanup_expired_sessions",
        "schedule": 86400.0,
    },
}

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    """Simple test task — prints request info."""
    print(f"Request: {self.request!r}")
