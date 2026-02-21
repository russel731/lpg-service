from pydantic import BaseModel
from typing import Optional


class OwnerCreate(BaseModel):
    telegram_id: int
    phone: str
    station_name: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
