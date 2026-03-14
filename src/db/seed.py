"""
Database seed function — inserts default rows into dimension tables.

Idempotent: safe to call on every server startup. Only inserts rows
that don't already exist (checks by unique key before inserting).
"""

from sqlalchemy.orm import Session
from src.events.model import EventTypes
from src.db.referrals import ReferralSources
from src.db.constants import EVENT_TYPES


def seed_defaults(db: Session) -> None:
    """
    Seed all default dimension values. Call once at app startup.
    Idempotent: safe to call on every startup, only inserts missing rows.
    """

    _seed_event_types(db)
    _seed_default_referral(db)

    print("\n\n=== Database SEED data verified and inserted if needed ===\n\n")


def _seed_event_types(db: Session) -> None:
    """
    Ensure all default event types exist in d_event_types.
    """

    existing = {et.name for et in db.query(EventTypes).all()}

    new_types = [
        EventTypes(name=name)
        for name in EVENT_TYPES
        if name not in existing
    ]

    if new_types:
        db.add_all(new_types)
        db.commit()
        print(
            f"   Seeded {len(new_types)} event types: {[t.name for t in new_types]}")
    else:
        print("   Event types already seeded")


def _seed_default_referral(db: Session) -> None:
    """
    Ensure a default 'direct' referral source exists for events with no referrer.
    """

    existing = db.query(ReferralSources).filter_by(
        source="direct",
        category="direct"
    ).first()

    if not existing:
        default_referral = ReferralSources(
            source="direct",
            referrer_url=None,
            category="direct"
        )
        db.add(default_referral)
        db.commit()
        print("Seeded default 'direct' referral source")

    else:
        print("Default referral source already seeded")
