from sqlalchemy import Column, Integer, String
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Mapped, mapped_column
from typing import Literal
from .base import Base
# Pydantic models for serialization


class DeviceTypes(Base):
    __tablename__ = "d_device_types"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    os: Mapped[Literal["Android", "iOS", "Windows"]
               ] = mapped_column(nullable=False)
    device_type: Mapped[str] = mapped_column(nullable=False)


class DeviceTypesBase(BaseModel):
    id: int
    os: Literal["Android", "iOS", "Windows"]
    device_type: str


class DeviceTypesCreate(DeviceTypesBase):
    pass


class DeviceTypesRead(DeviceTypesBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
