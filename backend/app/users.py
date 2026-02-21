from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models import User

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/set-language")
def set_language(telegram_id: int, language: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if not user:
        user = User(telegram_id=telegram_id, language=language)
        db.add(user)
    else:
        user.language = language

    db.commit()
    return {"status": "ok"}


@router.get("/get-language")
def get_language(telegram_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()

    if user:
        return {"language": user.language}

    return {"language": "kz"}