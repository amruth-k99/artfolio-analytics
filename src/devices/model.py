from sqlalchemy import Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import Base


class DeviceTypes(Base):
    __tablename__ = "d_device_types"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    os: Mapped[str] = mapped_column(nullable=False)
    device_type: Mapped[str] = mapped_column(nullable=False)
    browser: Mapped[str] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint('os', 'device_type', 'browser',
                         name='uix_os_device_type_browser'),
    )
