from .base import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Integer
from pydantic import BaseModel
from typing import Optional
import datetime


class Dates(Base):
    __tablename__ = "d_dates"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    date: Mapped[datetime.datetime] = mapped_column(
        DateTime, index=True, nullable=False)
    minute: Mapped[int] = mapped_column(nullable=False)
    hour: Mapped[int] = mapped_column(nullable=False)
    day: Mapped[int] = mapped_column(nullable=False)
    day_of_week: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int] = mapped_column(nullable=False)
    quarter: Mapped[int] = mapped_column(nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)


class DateModel(BaseModel):
    date: datetime.datetime
    minute: int
    hour: int
    day: int
    day_of_week: int
    month: int
    quarter: int
    year: int


class DateCreate(DateModel):
    pass


class DateUpdate(BaseModel):
    # optional fields for update
    date: Optional[datetime.datetime] = None
    minute: Optional[int] = None
    hour: Optional[int] = None
    day: Optional[int] = None
    day_of_week: Optional[int] = None
    month: Optional[int] = None
    quarter: Optional[int] = None
    year: Optional[int] = None


class DateDelete(BaseModel):
    id: int
