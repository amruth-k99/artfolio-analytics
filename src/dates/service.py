"""
Date dimension service — resolves timestamps into d_dates rows.
"""

import datetime
from sqlalchemy.orm import Session
from src.dates.model import Dates
from src.cache import cache_manager


def resolve_date(timestamp: datetime.datetime, db: Session) -> int:
    """
    Decompose a timestamp into d_dates dimension fields.
    Upsert by the full datetime value.

    Cache layer: rounded timestamp string → date_id.
    Returns the date_id.
    """
    date_cache = cache_manager.get_cache("dates")

    # Round down to the nearest minute for better performance and deduplication
    timestamp = timestamp.replace(second=0, microsecond=0)
    cache_key = timestamp.isoformat()

    # Cache hit — skip DB query
    cached = date_cache.get(cache_key)
    if cached is not None:
        return cached

    existing = db.query(Dates).filter_by(date=timestamp).first()
    if existing:
        date_cache.put(cache_key, existing.id)
        return existing.id

    new_date = Dates(
        date=timestamp,
        minute=timestamp.minute,
        hour=timestamp.hour,
        day=timestamp.day,
        day_of_week=timestamp.weekday(),  # 0=Monday, 6=Sunday
        month=timestamp.month,
        quarter=(timestamp.month - 1) // 3 + 1,
        year=timestamp.year
    )

    db.add(new_date)
    db.flush()

    date_cache.put(cache_key, new_date.id)
    return new_date.id
