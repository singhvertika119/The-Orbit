# pyrefly: ignore [missing-import]
from celery import Celery
# pyrefly: ignore [missing-import]
from celery.schedules import crontab
from app.core.config import settings
import ssl

# Initialize Celery app
redis_url = settings.REDIS_URL
ssl_conf = {}
if redis_url.startswith("rediss://"):
    ssl_conf = {
        "broker_use_ssl": {
            "ssl_cert_reqs": ssl.CERT_NONE
        },
        "redis_backend_use_ssl": {
            "ssl_cert_reqs": ssl.CERT_NONE
        }
    }

celery_app = Celery(
    "gigai",
    broker=redis_url,
    backend=redis_url,
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
    },
    **ssl_conf
)
