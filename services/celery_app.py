from celery import Celery
from core.config import settings

# the main celery app, we cannot use FAST API
celery_app = Celery(
    "url_shortener",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["services.background_tasks"],
)
