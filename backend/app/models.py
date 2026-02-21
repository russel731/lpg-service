from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


# 🔥 Заявки владельцев станций
class OwnerRequest(Base):
    __tablename__ = "owner_requests"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Telegram ID обязательно
    telegram_id = Column(Integer, nullable=False, index=True)

    phone = Column(String, nullable=False)
    station_name = Column(String, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)