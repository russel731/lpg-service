from pydantic import BaseModel


class OwnerCreate(BaseModel):
    telegram_id: int
    phone: str
    station_name: str
    latitude: float
    longitude: float