# this is our main processor for the stats
from sqlalchemy import func
from sqlalchemy.orm import Session

# this is calculating the date
import time
from datetime import datetime, timedelta, timezone

# for accessing DB
from models.models import Link, Click

# for getting cache data
from services.cache import r
import json


def get_link_id(short_code: str, db: Session) -> int | None:
    """Safely gets link_id from Redis cache or falls back to DB query."""
    cached_data = r.get(short_code)
    if cached_data:
        return json.loads(cached_data)["id"]

    link = db.query(Link).filter(Link.short_code == short_code).first()
    if not link:
        return None

    r.set(
        short_code,
        json.dumps({"id": link.id, "long_url": link.long_url}),
        ex=3600,
    )
    return link.id


def count_em_up(short_code: str, db: Session) -> int | None:
    # we use the above function to get the link id we need so no need to repeat code
    link_id = get_link_id(short_code, db)
    if link_id is None:
        return None
    return db.query(func.count(Click.id)).filter(Click.link_id == link_id).scalar()


def count_em_hr(short_code: str, limit_hrs: int, db: Session) -> int | None:
    # in the case we are given a time limit
    link_id = get_link_id(short_code, db)
    if link_id is None:
        return None

    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=limit_hrs)

    return (
        db.query(func.count(Click.id))
        .filter(Click.link_id == link_id, Click.created_at >= cutoff_time)
        .scalar()
    )


def daily_counts(short_code: str, db: Session) -> list[dict] | None:
    link_id = get_link_id(short_code, db)
    if link_id is None:
        return None
    # this is done for our chats for trendlines and shi
    daily_clicks = (
        db.query(
            func.date(Click.created_at).label("date"),
            func.count(Click.id).label("clicks"),
        )
        .filter(Click.link_id == link_id)
        .group_by(func.date(Click.created_at))
        .order_by(func.date(Click.created_at).desc())
        .all()
    )

    return [{"date": str(row.date), "clicks": row.clicks} for row in daily_clicks]
