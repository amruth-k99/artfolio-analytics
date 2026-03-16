
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from src.config import CONFIG

DATABASE_URL = CONFIG.database_url
SECRET_KEY = CONFIG.secret_key


class Base(DeclarativeBase):
    pass


# Set to True for debugging
engine = create_engine(DATABASE_URL, echo=False, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
