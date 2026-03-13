
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from ..config import CONFIG

DATABASE_URL = CONFIG.database_url
SECRET_KEY = CONFIG.secret_key

print(f"Using database URL: {DATABASE_URL}, SECRET_KEY: {CONFIG}")


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, bind=engine)
