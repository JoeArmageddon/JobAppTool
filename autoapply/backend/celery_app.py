"""Celery application configuration."""

import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")

app = Celery(
    "autoapply",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.scrape_worker", "workers.apply_worker"],
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "workers.scrape_worker.*": {"queue": "scrape"},
        "workers.apply_worker.*": {"queue": "apply"},
    },
)

app.conf.beat_schedule = {
    "scrape-jobs-every-6-hours": {
        "task": "workers.scrape_worker.run_job_scrape_for_all_active_profiles",
        "schedule": crontab(minute=0, hour="*/6"),
    },
}
