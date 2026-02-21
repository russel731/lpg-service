from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Owner(Base):
    __tablename__ = "owners"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, index=True)
    phone = Column(String)
    station_name = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    status = Column(String, default="pending")