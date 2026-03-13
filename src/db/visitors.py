from typing_extensions import Literal

from .base import Base
from sqlalchemy import String, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
import datetime
from pydantic import BaseModel


class Visitors(Base):
    __tablename__ = "d_visitors"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    visitor_type: Mapped[Literal["new", "returning"]
                         ] = mapped_column(nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    session_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    signup_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, index=True, nullable=True)
    account_status: Mapped[Literal["active", "inactive", "deleted"]
                           ] = mapped_column(nullable=False)
    portfolio_created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, index=True, nullable=True)
    user_type: Mapped[Literal["guest", "user", "admin"]
                      ] = mapped_column(nullable=False)


class VisitorModel(BaseModel):
    visitor_type: Literal["new", "returning"]
    user_id: str | None
    session_id: str
    signup_date: datetime.datetime | None
    account_status: Literal["active", "inactive", "deleted"]
    portfolio_created_at: datetime.datetime | None
    user_type: Literal["guest", "user", "admin"]


class VisitorCreate(VisitorModel):
    pass


class VisitorUpdate(VisitorModel):
    pass


class VisitorDelete(VisitorModel):
    id: str
