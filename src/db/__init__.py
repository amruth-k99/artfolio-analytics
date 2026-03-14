from src.db.base import Base, SessionLocal, engine
from .page import Page
from .date import Dates
from .device_types import DeviceTypes
from src.visitors.model import Visitors
from src.locations.model import Locations
from .referrals import ReferralSources
from src.events.model import Events, EventTypes


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
