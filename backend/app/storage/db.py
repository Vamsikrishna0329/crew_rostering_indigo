
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.settings import settings
DATABASE_URL = f"sqlite:///{settings.sqlite_path}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
