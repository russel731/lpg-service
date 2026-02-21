from fastapi import APIRouter, HTTPException
from app.models.database import SessionLocal
from app.models.owner import Owner

router = APIRouter()

@router.post("/approve-owner/{owner_id}")
def approve_owner(owner_id: int):
    db = SessionLocal()
    owner = db.query(Owner).filter(Owner.id == owner_id).first()

    if not owner:
        db.close()
        raise HTTPException(status_code=404, detail="Владелец не найден")

    owner.is_approved = True
    db.commit()
    db.close()

    return {
        "status": "ok",
        "message": f"Владелец {owner_id} подтверждён"
    }
