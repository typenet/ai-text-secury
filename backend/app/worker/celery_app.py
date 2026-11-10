from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "secury", broker=settings.redis_url, backend=settings.redis_url, include=["app.worker.tasks"]
)
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    task_soft_time_limit=240,
    task_serializer="json",
    accept_content=["json"],
)
