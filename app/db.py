import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

url = os.getenv("APP_DATABASE_URL") or os.getenv("DATABASE_URL")
if not url:
    raise RuntimeError("DATABASE_URL / APP_DATABASE_URL not set")

engine = create_engine(url=url, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)