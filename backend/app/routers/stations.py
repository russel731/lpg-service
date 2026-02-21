from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Station
from math import radians, cos, sin, sqrt, atan2

router = APIRouter(prefix="/stations", tags=["stations"])


def distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))

    return round(R * c, 2)


@router.get("/nearby")
def nearby(lat: float, lon: float, db: Session = Depends(get_db)):
    stations = db.query(Station).all()

    result = []

    for st in stations:
        dist = distance(lat, lon, st.latitude, st.longitude)

        result.append({
            "id": st.id,
            "name": st.name,
            "distance": dist
        })

    result.sort(key=lambda x: x["distance"])

    return result[:10]