"""
Global dimension registry — caches DB lookups at startup so the
ingestion pipeline never needs to hit the DB for known dimension IDs.

Usage:
    from src.db.registry import registry

    # Direct attribute access (IDE autocomplete, no typos):
    registry.PAGE_VIEW      # → 1
    registry.CLICK           # → 2

    # Or dynamic lookup by string:
    registry.get_event_type_id("PAGE_VIEW")  # → 1

    # Default referral:
    registry.DIRECT_REFERRAL_ID  # → 1

"""

from sqlalchemy.orm import Session
from src.events.model import EventTypes
from src.referrals.model import ReferralSources


class DimensionRegistry:
    """
    Singleton that holds cached dimension lookups.
    Loaded once at app startup via registry.load(db).

    After load(), each event type is available as a direct attribute:
        registry.PAGE_VIEW  → int (the DB id)
        registry.CLICK      → int
        registry.LOGIN      → int
        ...
    """

    def __init__(self):
        # { "PAGE_VIEW": 1, "CLICK": 2, ... }
        self.event_types: dict[str, int] = {}
        # Direct ID attributes (set during load)
        self.PAGE_VIEW: int = 0
        self.CLICK: int = 0
        self.LOGIN: int = 0
        self.LOGOUT: int = 0
        self.REGISTER: int = 0
        self.PORTFOLIO_CREATED: int = 0
        self.PORTFOLIO_UPDATED: int = 0
        self.PORTFOLIO_DELETED: int = 0
        self.PORTFOLIO_VIEWED: int = 0

        self.DIRECT_REFERRAL_ID: int = 0  # Default referral
        self._loaded = False

    def load(self, db: Session) -> None:
        """
        Load all cached lookups from the database. Call once at startup.
        """

        self._load_event_types(db)
        self._load_default_referral(db)
        self._loaded = True
        print(
            f"\n\n=== Registry loaded: {len(self.event_types)} event types cached ===\n\n")

    def _load_event_types(self, db: Session) -> None:
        """
        Cache all event types as dict AND as direct attributes.
        """

        rows = db.query(EventTypes).all()
        self.event_types = {row.name: row.id for row in rows}

        # Set each as a direct attribute: registry.PAGE_VIEW = 1, etc.
        for name, id_ in self.event_types.items():
            setattr(self, name, id_)

    def _load_default_referral(self, db: Session) -> None:
        """
        Cache the default 'direct' referral source ID.
        This is used for events with no referrer, so we don't have to query the DB every time.
        """

        row = db.query(ReferralSources).filter_by(
            source="direct", category="direct"
        ).first()

        if row:
            self.DIRECT_REFERRAL_ID = row.id

    def get_event_type_id(self, name: str) -> int:
        """
        Get the cached ID for an event type by name (dynamic lookup).
        Raises KeyError if the event type doesn't exist.
        """
        if name not in self.event_types:
            raise KeyError(
                f"Event type '{name}' not found in registry. "
                f"Available: {list(self.event_types.keys())}"
            )
        return self.event_types[name]

    def get_default_referral_id(self) -> int:
        """
        Get the cached ID of the default 'direct' referral source.
        """

        if self.DIRECT_REFERRAL_ID == 0:
            raise RuntimeError(
                "Default referral ID not loaded. Was registry.load() called?")

        return self.DIRECT_REFERRAL_ID

    def is_loaded(self) -> bool:
        return self._loaded


# Global singleton — import this everywhere (loads only once at startup, saves DB lookups on every event)
registry = DimensionRegistry()
