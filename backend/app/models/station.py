from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)

    owner_id = Column(Integer, nullable=False)

    station_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    gas_status = Column(String, default="unknown")

    created_at = Column(DateTime, default=datetime.utcnow)