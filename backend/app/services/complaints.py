from sqlalchemy.orm import Session
from app.models.complaints import Complaint
from app.models.station import Station


MAX_COMPLAINTS = 3


def add_complaint(db: Session, user_id: int, station_id: int):
    # Проверка: уже жаловался?
    existing = db.query(Complaint).filter(
        Complaint.user_id == user_id,
        Complaint.station_id == station_id
    ).first()

    if existing:
        return {"message": "Вы уже жаловались на эту станцию"}

    complaint = Complaint(
        user_id=user_id,
        station_id=station_id
    )

    db.add(complaint)
    db.commit()

    # Считаем жалобы
    count = db.query(Complaint).filter(
        Complaint.station_id == station_id
    ).count()

    # Если много жалоб → блокируем управление
    if count >= MAX_COMPLAINTS:
        station = db.query(Station).get(station_id)
        station.gas_status = "unknown"
        db.commit()

    return {"message": "Жалоба принята", "count": count}