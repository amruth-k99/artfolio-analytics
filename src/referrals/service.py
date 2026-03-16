"""
Referral dimension service — resolves referral info into d_referral_sources rows.
"""

from sqlalchemy.orm import Session
from src.referrals.model import ReferralSources
from src.events.schema import ReferralPayload
from src.db.registry import registry
from src.cache import cache_manager


def resolve_referral(referral: ReferralPayload, db: Session) -> int:
    """
    Upsert referral source by (source, referrer_url, category).
    Falls back to the seeded 'direct' referral if no referral data provided.

    Cache layer: (source, referrer_url, category) → referral_id.
    Returns the referral_id.
    """

    # If it's a plain direct visit, use the pre-seeded default (already cached in registry)
    if referral.source == "direct" and referral.referrer_url is None:
        return registry.get_default_referral_id()

    referral_cache = cache_manager.get_cache("referrals")
    cache_key = f"{referral.source}|{referral.referrer_url}|{referral.category}"

    # Cache hit — skip DB query
    cached = referral_cache.get(cache_key)
    if cached is not None:
        return cached

    existing = db.query(ReferralSources).filter_by(
        source=referral.source,
        referrer_url=referral.referrer_url,
        category=referral.category
    ).first()

    if existing:
        referral_cache.put(cache_key, existing.id)
        return existing.id

    new_referral = ReferralSources(
        source=referral.source,
        referrer_url=referral.referrer_url,
        category=referral.category
    )

    db.add(new_referral)
    db.flush()

    referral_cache.put(cache_key, new_referral.id)
    return new_referral.id
