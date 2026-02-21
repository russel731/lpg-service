from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(prefix="/stations", tags=["stations"])


@router.get("/")
def get_stations(db: Session = Depends(get_db)):
    result = db.execute("SELECT 1").fetchone()
    return {"database": "connected", "test": result[0]}