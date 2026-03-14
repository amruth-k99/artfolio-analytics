from typing_extensions import Literal

from src.db.base import Base
from sqlalchemy import String, DateTime, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
import datetime


class Visitors(Base):
    __tablename__ = "d_visitors"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    visitor_type: Mapped[Literal["new", "returning"]
                         ] = mapped_column(nullable=False)
    user_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    device_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    signup_date: Mapped[datetime.datetime] = mapped_column(
        DateTime, index=True, nullable=True)
    account_status: Mapped[Literal["active", "inactive", "deleted"]
                           ] = mapped_column(nullable=False)
    portfolio_created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, index=True, nullable=True)
    user_type: Mapped[Literal["guest", "user", "admin"]
                      ] = mapped_column(nullable=False)

    # unique by user_id, device_id
    __table_args__ = (
        UniqueConstraint('user_id', 'device_id', name='uq_user_device'),
    )
