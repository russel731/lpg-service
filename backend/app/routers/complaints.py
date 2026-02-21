from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.complaints import add_complaint

router = APIRouter(prefix="/complaints", tags=["Complaints"])


@router.post("/")
def create_complaint(
    user_id: int,
    station_id: int,
    db: Session = Depends(get_db)
):
    return add_complaint(db, user_id, station_id)