from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Owner
from app.schemas.owner import OwnerCreate

router = APIRouter(prefix="/owners", tags=["Owners"])


# ✅ Создание владельца
@router.post("/")
def create_owner(owner: OwnerCreate, db: Session = Depends(get_db)):
    # Проверяем, существует ли уже
    existing = db.query(Owner).filter(Owner.telegram_id == owner.telegram_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Owner already exists")

    db_owner = Owner(
        telegram_id=owner.telegram_id,
        phone=owner.phone,
        station_name=owner.station_name,
        latitude=owner.latitude,
        longitude=owner.longitude,
    )

    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)

    return {
        "status": "ok",
        "id": db_owner.id
    }


# ✅ Получить владельца по telegram_id (основа авторизации)
@router.get("/{telegram_id}")
def get_owner(telegram_id: int, db: Session = Depends(get_db)):
    owner = db.query(Owner).filter(Owner.telegram_id == telegram_id).first()

    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    return {
        "id": owner.id,
        "telegram_id": owner.telegram_id,
        "phone": owner.phone,
        "station_name": owner.station_name,
        "latitude": owner.latitude,
        "longitude": owner.longitude,
        "status": owner.status,
    }