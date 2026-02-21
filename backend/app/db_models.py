from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime

# 🔥 ВАЖНО: используем Base из database
from app.database import Base


# 🔥 Заявки владельцев станций
class OwnerRequest(Base):
    __tablename__ = "owner_requests"

    id = Column(Integer, primary_key=True, index=True)

    # 🔥 Telegram ID
    telegram_id = Column(Integer, nullable=False, index=True)

    phone = Column(String, nullable=False)
    station_name = Column(String, nullable=False)

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    status = Column(String, default="pending")

    created_at = Column(DateTime, default=datetime.utcnow)
