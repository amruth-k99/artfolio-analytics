"""
Referral dimension service — resolves referral info into d_referral_sources rows.
"""

from sqlalchemy.orm import Session
from src.referrals.model import ReferralSources
from src.events.schema import ReferralPayload
from src.db.registry import registry


def resolve_referral(referral: ReferralPayload, db: Session) -> int:
    """
    Upsert referral source by (source, referrer_url, category).
    Falls back to the seeded 'direct' referral if no referral data provided.
    Returns the referral_id.
    """

    # If it's a plain direct visit, use the pre-seeded default
    if referral.source == "direct" and referral.referrer_url is None:
        return registry.get_default_referral_id()

    existing = db.query(ReferralSources).filter_by(
        source=referral.source,
        referrer_url=referral.referrer_url,
        category=referral.category
    ).first()

    if existing:
        return existing.id

    new_referral = ReferralSources(
        source=referral.source,
        referrer_url=referral.referrer_url,
        category=referral.category
    )

    db.add(new_referral)
    db.flush()
    return new_referral.id
