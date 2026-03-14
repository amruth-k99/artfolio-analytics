from sqlalchemy import Integer, UniqueConstraint
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
# Pydantic models for serialization


class DeviceTypes(Base):
    __tablename__ = "d_device_types"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    os: Mapped[str] = mapped_column(nullable=False)
    device_type: Mapped[str] = mapped_column(nullable=False)
    browser: Mapped[str] = mapped_column(nullable=False)

    # unique constraint on os, device_type, and browser
    __table_args__ = (
        UniqueConstraint('os', 'device_type', 'browser',
                         name='uix_os_device_type_browser'),
    )


class DeviceTypesBase(BaseModel):
    os: str
    device_type: str
    browser: str


class DeviceTypesCreate(DeviceTypesBase):
    pass


class DeviceTypesRead(DeviceTypesBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
