from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import OwnerRequest
from app.schemas.owner import OwnerCreate

router = APIRouter(prefix="/owners", tags=["Owners"])


@router.post("/")
def create_owner(data: OwnerCreate, db: Session = Depends(get_db)):

    owner = OwnerRequest(
        telegram_id=data.telegram_id,  # 🔥 ОБЯЗАТЕЛЬНО
        phone=data.phone,
        station_name=data.station_name,
        latitude=data.latitude,
        longitude=data.longitude,
    )

    db.add(owner)
    db.commit()
    db.refresh(owner)

    return {"status": "ok", "id": owner.id}