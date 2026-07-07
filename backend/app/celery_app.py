from celery import Celery

from app.core.settings import settings

celery = Celery(
    main="app",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker"],
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

celery.conf.beat_schedule = {
    "dispatch-notifications-every-30s": {
        "task": "beat_dispatch_notifications",
        "schedule": 30.0,
    },
}
