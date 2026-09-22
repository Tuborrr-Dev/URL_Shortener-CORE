from models.models import User, Link
from services.shortener import shorten_B62
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# this is calculating the date
from datetime import datetime, timezone

# for cachihne
from services.cache import r
import json

# for background jobs
from services.background_tasks import log_clicks


# now we create an entire function to do all our CRUD processes for us
def shorten(user_id: str, long_url: str, db: Session) -> str:
    # 0. check if anything is in url
    if long_url is None:
        return None
    # Check if THIS specific user have stored the exact same URL before, we dont want to store the same thing, save space
    existing_link = (
        db.query(Link)
        .filter(Link.long_url == long_url, Link.user_id == user_id)
        .first()
    )
    if existing_link:
        return existing_link.short_code
    max_retries = 3
    for x in range(max_retries):
        try:
            short_cd = shorten_B62()
            new_link = Link(short_code=short_cd, long_url=long_url, user_id=user_id)
            db.add(new_link)
            db.commit()
            # return the short code, after storing in Postgres
            return short_cd
        # in the case where it has been stored the integrityError is raised and the entire process is roll-backed
        except IntegrityError:
            db.rollback()
    # and if after 3 tries it still shows DB has what we used we return none
    return None


def elongate(short_code: str, refer_url: str, iphash: str, db: Session) -> str | None:
    link_id = None
    long_url = None
    cached_data = r.get(short_code)
    if cached_data:  # <-- then we have it in the cache
        data = json.loads(cached_data)
        link_id = data["id"]
        long_url = data["long_url"]
    # not in cache so check in Link and get long url from DB
    else:
        link = db.query(Link).filter(Link.short_code == short_code).first()
        if not link:  # not in that bih
            return None
        long_url = link.long_url
        link_id = link.id
        # we now have the long link so lets cache in json form
        r.set(
            short_code,
            json.dumps({"id": link_id, "long_url": long_url}),
            ex=3600,
        )  # <-- TTL is 1 hour
    # we need to save the actual datetime to avoid celery fucking us up in case theres an outage or anything else
    click_time = datetime.now(
        timezone.utc
    ).isoformat()  # <-- ISO 8601 strings ("2026-09-17T22:45:00+00:00") safely serialize through Redis/Celery's default JSON serializer without epoch/timezone offset bugs.
    # above all else after confirming a link exists now a count should exist towards its clicks
    log_clicks.delay(
        link_id=link_id, clicked_at=click_time, referrer=refer_url, ip_hash=iphash
    )  # <-- we now save the date time in epoch
    return long_url
