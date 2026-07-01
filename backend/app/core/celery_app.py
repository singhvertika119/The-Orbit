# pyrefly: ignore [missing-import]
from celery import Celery
# pyrefly: ignore [missing-import]
from celery.schedules import crontab
from app.core.config import settings

# Initialize Celery app
celery_app = Celery(
    "gigai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.invoices",
        "app.tasks.followups",
        "app.tasks.digest"
    ]
)

# Standard configurations and Beat scheduler mapping
celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    beat_schedule={
        "daily-overdue-check": {
            "task": "app.tasks.followups.daily_overdue_check",
            "schedule": crontab(hour=2, minute=30)  # 2:30 AM UTC = 8:00 AM IST
        },
        "morning-digest": {
            "task": "app.tasks.digest.morning_digest",
            "schedule": crontab(hour=2, minute=30)  # 2:30 AM UTC = 8:00 AM IST
        }
    }
)
