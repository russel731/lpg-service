from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

from app.database import Base


class OwnerRequest(Base):
    __tablename__ = "owner_requests"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, nullable=False)
    station_name = Column(String, nullable=False)

    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    status = Column(String, default="pending")  # pending / approved / rejected
    created_at = Column(DateTime, default=datetime.utcnow)