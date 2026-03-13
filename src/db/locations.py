from .base import Base
from sqlalchemy import String, UniqueConstraint, Integer
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel


class Locations(Base):
    __tablename__ = "d_locations"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    city: Mapped[str] = mapped_column(String, index=True, nullable=False)
    state: Mapped[str] = mapped_column(String, index=True, nullable=False)
    country: Mapped[str] = mapped_column(String, index=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('city', 'state', 'country',
                         name='uq_city_state_country'),
    )


class LocationModel(BaseModel):
    city: str
    state: str
    country: str
