from pydantic import BaseModel
from typing import Optional
import datetime


class DateModel(BaseModel):
    id: int | None = None
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
