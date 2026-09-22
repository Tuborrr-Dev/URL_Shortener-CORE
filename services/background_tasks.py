from database import (
    SessionLocal,
)  # <-- we have to use a seperate connection since this is a diff task
from models.models import Click
from services.celery_app import celery_app
from sqlalchemy.exc import OperationalError
from datetime import datetime


@celery_app.task(
    autoretry_for=(OperationalError,),  # Retry on DB connection drop
    retry_kwargs={"max_retries": 5},  # Try up to 5 times
    retry_backoff=True,  # Exponential backoff (2s, 4s, 8s...)
    retry_backoff_max=600,  # Cap wait time at 10 minutes
)
def log_clicks(link_id: int, created_at: str, referrer: str | None, ip_hash: str):
    db = SessionLocal()  # Standalone session for worker thread
    try:
        new_click = Click(
            link_id=link_id,
            created_at=datetime.fromisoformat(
                created_at
            ),  # <-- Overrides server_default since we already stored the date time in the original url processing
            referrer=referrer,
            ip_hash=ip_hash,
        )
        db.add(new_click)
        db.commit()
    finally:
        db.close()
