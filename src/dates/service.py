"""
Date dimension service — resolves timestamps into d_dates rows.
"""

import datetime
from sqlalchemy.orm import Session
from src.dates.model import Dates


def resolve_date(timestamp: datetime.datetime, db: Session) -> int:
    """
    Decompose a timestamp into d_dates dimension fields.
    Upsert by the full datetime value.
    Returns the date_id.
    """

    # Round down to the nearest minute for better performance and deduplication
    timestamp = timestamp.replace(second=0, microsecond=0)
    existing = db.query(Dates).filter_by(date=timestamp).first()
    if existing:
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
    return new_date.id
