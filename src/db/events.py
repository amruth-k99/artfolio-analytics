from .base import Base
from sqlalchemy import ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
import datetime


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
    referral_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("d_referral_sources.id"), nullable=False)
    datetime: Mapped[datetime.datetime] = mapped_column(
        DateTime, nullable=True)
