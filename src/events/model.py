from src.db.base import Base
from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime


class EventTypes(Base):
    __tablename__ = "d_event_types"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)


class Events(Base):
    __tablename__ = "f_events"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    date_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_dates.id"), nullable=False)
    device_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_device_types.id"), nullable=False)
    visitor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_visitors.id"), nullable=False)
    location_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_locations.id"), nullable=False)
    page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_pages.id"), nullable=False)
    referral_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_referral_sources.id"), nullable=False)
    datetime: Mapped[datetime] = mapped_column(
        DateTime, nullable=False)
    session_id: Mapped[str] = mapped_column(String, nullable=False)
    event_type_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_event_types.id"), nullable=False)
    properties: Mapped[str] = mapped_column(String, nullable=True)

    # Relationships to dimension tables
    device_type = relationship("DeviceTypes", lazy="joined")
    visitor = relationship("Visitors", lazy="joined")
    location = relationship("Locations", lazy="joined")
    page = relationship("Page", lazy="joined")
    referral = relationship("ReferralSources", lazy="joined")
    event_type = relationship("EventTypes", lazy="joined")
