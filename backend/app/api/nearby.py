from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import math

router = APIRouter()


class NearbyRequest(BaseModel):
    lat: float
    lon: float


class Station(BaseModel):
    id: int
    name: str
    lat: float
    lon: float
    price: float
    distance_km: float


STATIONS = [
    {"id": 1, "name": "LPG Station 1", "lat": 43.238949, "lon": 76.889709, "price": 210},
    {"id": 2, "name": "LPG Station 2", "lat": 43.250000, "lon": 76.920000, "price": 205},
    {"id": 3, "name": "LPG Station 3", "lat": 43.220000, "lon": 76.870000, "price": 215},
]


def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@router.post("/nearby", response_model=List[Station])
def get_nearby_stations(data: NearbyRequest):
    results = []

    for station in STATIONS:
        distance = calculate_distance(
            data.lat, data.lon, station["lat"], station["lon"]
        )

        results.append(
            Station(
                id=station["id"],
                name=station["name"],
                lat=station["lat"],
                lon=station["lon"],
                price=station["price"],
                distance_km=round(distance, 2),
            )
        )

    results.sort(key=lambda x: x.distance_km)

    return results