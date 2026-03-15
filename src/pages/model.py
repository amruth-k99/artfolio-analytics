from src.db.base import Base
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column


class Page(Base):
    __tablename__ = "d_pages"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    page_name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    url: Mapped[str] = mapped_column(String, index=True, nullable=False)
    full_path: Mapped[str] = mapped_column(String, index=True, nullable=False)
    host: Mapped[str] = mapped_column(String, index=True, nullable=False)
