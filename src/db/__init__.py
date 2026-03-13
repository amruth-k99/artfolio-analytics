from .base import Base, SessionLocal, engine
from .page import Page
from .date import Dates
from .device_types import DeviceTypes
from .visitors import Visitors
from .locations import Locations
from .referrals import ReferralSources
from ..events.model import Events


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
