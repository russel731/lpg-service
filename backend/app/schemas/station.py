from pydantic import BaseModel


class StationBase(BaseModel):
    name: str
    lat: float
    lon: float
    status: str


class StationResponse(StationBase):
    id: int


class StationUpdate(StationBase):
    pass