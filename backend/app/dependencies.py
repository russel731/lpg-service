from app.database import get_db

__all__ = ["get_db"]

from sqlalchemy.orm import sessionmaker, Session

from .database import engine

# Создаём фабрику сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Зависимость для FastAPI
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
