from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "openleads",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.leads", "app.workers.email", "app.workers.campaigns", "app.workers.enrichment", "app.workers.linkedin", "app.workers.whatsapp"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,
    task_soft_time_limit=25 * 60,
    worker_max_tasks_per_child=200,
    beat_schedule={
        "daily-lead-cleanup": {
            "task": "app.workers.leads.cleanup_expired_leads",
            "schedule": 86400.0,
        },
        "daily-email-limit-reset": {
            "task": "app.workers.email.reset_daily_limits",
            "schedule": 86400.0,
        },
        "check-campaign-schedules": {
            "task": "app.workers.campaigns.check_scheduled_campaigns",
            "schedule": 300.0,
        },
    },
)
