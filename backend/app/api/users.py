from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/")
def create_user(telegram_id: str, role: str, language: str = "ru", db: Session = Depends(get_db)):
    user = User(
        telegram_id=telegram_id,
        role=role,
        language=language
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user