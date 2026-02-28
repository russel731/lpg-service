from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/set-language")
def set_language(telegram_id: int, language: str, db: Session = Depends(get_db)):
    """
    Сохраняем язык пользователя
    """
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()

    if not user:
        user = models.User(
            telegram_id=telegram_id,
            language=language
        )
        db.add(user)
    else:
        user.language = language

    db.commit()
    return {"status": "ok"}


@router.get("/{telegram_id}")
def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """
    Получить пользователя
    """
    user = db.query(models.User).filter(
        models.User.telegram_id == telegram_id
    ).first()
docker compose up --build
    if not user:
        return {"user": None}

    return {
        "telegram_id": user.telegram_id,
        "language": user.language
    }