from app.database import Base, engine

# важно: импортируем ВСЕ модели
from app.models import User, Station


def init_db():
    Base.metadata.create_all(bind=engine)