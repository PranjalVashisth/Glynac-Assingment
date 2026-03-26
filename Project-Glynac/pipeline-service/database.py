import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Read the database URL from the environment variable set in docker-compose.yml
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/customer_db"   # local fallback
)

# create_engine sets up the connection pool to PostgreSQL
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory – every time you call SessionLocal() you get a DB session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the parent class for all ORM models
Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a DB session and ensures it is
    closed after the request finishes (even if an error occurs).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
