from src.db.base import Base, SessionLocal, engine
from src.dates.model import Dates
from src.devices.model import DeviceTypes
from src.pages.model import Page
from src.referrals.model import ReferralSources
from src.visitors.model import Visitors
from src.locations.model import Locations


def init_db():
    """
    Create all tables. Called during app startup (lifespan) AFTER
    all ORM models have been imported and registered with Base.
    """
    # Import here to avoid circular imports at module level
    from src.events.model import Events, EventTypes  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
