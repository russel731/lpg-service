from backend.models import Base, Station
from backend.database import SessionLocal, engine
from models import Base, Station
from datetime import datetime


def seed():
    db: Session = SessionLocal()

    # очищаем старые данные
    db.query(Station).delete()

    stations = [
        Station(
            name="Газ Актал 1",
            lat=43.65,
            lon=51.16,
            gas_available=True,
            gas_low=False,
            owner_id=1,
            last_update=datetime.utcnow(),
        ),
        Station(
            name="Газ Актал 2",
            lat=43.66,
            lon=51.14,
            gas_available=True,
            gas_low=True,
            owner_id=1,
            last_update=datetime.utcnow(),
        ),
        Station(
            name="Газ Актал 3",
            lat=43.67,
            lon=51.15,
            gas_available=False,
            gas_low=False,
            owner_id=None,
            last_update=datetime.utcnow(),
        ),
    ]

    db.add_all(stations)
    db.commit()
    db.close()

    print("✅ Seed completed")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed()