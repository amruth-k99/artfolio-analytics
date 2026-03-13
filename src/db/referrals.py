from .base import Base, engine
from sqlalchemy import String, Integer
from typing import Literal
from sqlalchemy.orm import Mapped, mapped_column


class ReferralSources(Base):
    __tablename__ = "d_referral_sources"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(
        String, index=True, nullable=False, default="direct")
    referrer_url: Mapped[str] = mapped_column(
        String, index=True, nullable=True)
    category: Mapped[Literal["social", "search", "email", "direct", "other"]
                     ] = mapped_column(nullable=False, default="direct")
