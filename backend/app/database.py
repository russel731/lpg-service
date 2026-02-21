from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ВАЖНО: подключение к PostgreSQL внутри Docker
DATABASE_URL = "postgresql://lpg:lpg@postgres:5432/lpg"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


# Dependency для FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()