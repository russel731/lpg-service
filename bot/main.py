from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt
import bcrypt, httpx, asyncio, os, json, shutil, uuid

# ══════════════════════════════════════════
# КОНФИГ
# ══════════════════════════════════════════
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lpguser:lpgpass@localhost/lpgdb")
SECRET_KEY = os.getenv("SECRET_KEY", "lpg-secret-key-2026")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8482373207:AAGmeRGPBpiikO5mzxWuTJcVxsKDTTVc1CY")
UPLOAD_DIR = "uploads/photos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="АГЗС Мониторинг API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ══════════════════════════════════════════
# МОДЕЛИ БД
# ══════════════════════════════════════════

class Station(Base):
    __tablename__ = "stations"
    id            = Column(Integer, primary_key=True)
    name          = Column(String, nullable=False)
    lat           = Column(Float, nullable=False)
    lon           = Column(Float, nullable=False)
    status        = Column(String, default="green")       # green/yellow/red/purple
    last_updated  = Column(DateTime, default=datetime.utcnow)
    owner_id      = Column(Integer, ForeignKey("users.id"), nullable=True)

    # ПРЕМИУМ поля
    queue_level   = Column(Integer, default=0)            # 0-100
    services      = Column(JSON, default=list)            # ["wash","air","shop","cafe","tire","vacuum"]
    photos        = Column(JSON, default=list)            # ["url1", "url2", ...]
    reminder_min  = Column(Integer, default=120)          # интервал напоминания в минутах
    is_premium    = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    description   = Column(Text, nullable=True)

    owner         = relationship("User", back_populates="station", foreign_keys=[owner_id])
    trusted_users = relationship("TrustedUser", back_populates="station")
    subscriptions = relationship("Subscription", back_populates="station")


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    name          = Column(String, nullable=False)
    phone         = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="owner")       # owner/admin
    is_approved   = Column(Boolean, default=False)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=True)
    telegram_id   = Column(String, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    station       = relationship("Station", back_populates="owner", foreign_keys=[Station.owner_id])


class TrustedUser(Base):
    """До 3 доверенных пользователей на станцию — могут менять статус газа и очереди"""
    __tablename__ = "trusted_users"
    id            = Column(Integer, primary_key=True)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=False)
    telegram_id   = Column(String, nullable=False)
    name          = Column(String, nullable=False)
    added_at      = Column(DateTime, default=datetime.utcnow)
    added_by      = Column(Integer, ForeignKey("users.id"))

    station       = relationship("Station", back_populates="trusted_users")


class Subscription(Base):
    """Подписки клиентов на уведомления о газе"""
    __tablename__ = "subscriptions"
    id            = Column(Integer, primary_key=True)
    telegram_id   = Column(String, nullable=False)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    station       = relationship("Station", back_populates="subscriptions")


class ReminderLog(Base):
    """Лог отправленных напоминаний — чтобы не спамить"""
    __tablename__ = "reminder_logs"
    id            = Column(Integer, primary_key=True)
    station_id    = Column(Integer, nullable=False)
    sent_at       = Column(DateTime, default=datetime.utcnow)



class Complaint(Base):
    """Жалобы водителей на несоответствие статуса"""
    __tablename__ = "complaints"
    id            = Column(Integer, primary_key=True)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=False)
    telegram_id   = Column(String, nullable=True)   # None = анонимно
    # Ключ уникальности: один пользователь — одна жалоба пока статус не обновится
    status_snapshot = Column(String, nullable=False)  # статус на момент жалобы
    last_updated_snapshot = Column(String, nullable=True)  # lastUpdated на момент жалобы
    created_at    = Column(DateTime, default=datetime.utcnow)


class Settings(Base):
    """Глобальные настройки системы"""
    __tablename__ = "settings"
    key   = Column(String, primary_key=True)
    value = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# ══════════════════════════════════════════
# СХЕМЫ PYDANTIC
# ══════════════════════════════════════════

class UserRegister(BaseModel):
    name: str
    phone: str
    password: str
    station_id: Optional[int] = None
    telegram_id: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class StatusUpdate(BaseModel):
    status: str

class QueueUpdate(BaseModel):
    queue_level: int  # 0-100

class ServicesUpdate(BaseModel):
    services: List[str]

class ReminderUpdate(BaseModel):
    reminder_min: int  # 30/60/120/240/480

class TrustedUserAdd(BaseModel):
    telegram_id: str
    name: str

class StationCreate(BaseModel):
    name: str
    lat: float
    lon: float
    description: Optional[str] = None

class SubscribeRequest(BaseModel):
    telegram_id: str
    station_id: int

# ══════════════════════════════════════════
# ХЭЛПЕРЫ
# ══════════════════════════════════════════

def get_setting(db: Session, key: str, default: str = "") -> str:
    row = db.query(Settings).filter(Settings.key == key).first()
    return row.value if row else default

def set_setting(db: Session, key: str, value: str):
    row = db.query(Settings).filter(Settings.key == key).first()
    if row:
        row.value = value
    else:
        db.add(Settings(key=key, value=value))
    db.commit()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: int) -> str:
    return jwt.encode({"sub": str(user_id), "exp": datetime.utcnow() + timedelta(days=30)}, SECRET_KEY, algorithm="HS256")

def get_current_user(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user = db.query(User).filter(User.id == int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Неверный токен")

def get_station_status(station: Station) -> str:
    if station.status in ("green", "yellow", "red"):
        hours_since = (datetime.utcnow() - station.last_updated).total_seconds() / 3600
        if hours_since > 24:
            return "purple"
    return station.status

def station_to_dict(s: Station) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "lat": s.lat,
        "lon": s.lon,
        "status": get_station_status(s),
        "lastUpdated": s.last_updated.isoformat() if s.last_updated else None,
        "hasOwner": s.owner_id is not None,
        # Премиум поля (видны всем для отображения на карте)
        "queueLevel": s.queue_level,
        "services": s.services or [],
        "photos": s.photos or [],
        "isPremium": s.is_premium,
        "description": s.description,
        "complaintCount": s.complaint_count if hasattr(s, 'complaint_count') else 0,
    }

async def send_tg(chat_id: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        )

def require_owner(token: str, db: Session) -> tuple[User, Station]:
    """Получить авторизованного владельца и его станцию"""
    from fastapi.security import HTTPBearer
    user = get_current_user(token, db)
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Аккаунт не одобрен")
    station = db.query(Station).filter(Station.id == user.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    return user, station

def get_token_from_header(authorization: str) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не передан")
    return authorization[7:]

# ══════════════════════════════════════════
# РОУТЫ: СТАНЦИИ (публичные)
# ══════════════════════════════════════════

@app.get("/stations")
def list_stations(db: Session = Depends(get_db)):
    stations = db.query(Station).all()
    result = []
    for s in stations:
        d = station_to_dict(s)
        last_upd = s.last_updated.isoformat() if s.last_updated else ""
        d["complaintCount"] = db.query(Complaint).filter(
            Complaint.station_id == s.id,
            Complaint.last_updated_snapshot == last_upd
        ).count()
        d["complaintThreshold"] = int(get_setting(db, "complaint_threshold", "5"))
        result.append(d)
    return result

@app.get("/stations/{station_id}")
def get_station(station_id: int, db: Session = Depends(get_db)):
    s = db.query(Station).filter(Station.id == station_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    d = station_to_dict(s)
    last_upd = s.last_updated.isoformat() if s.last_updated else ""
    d["complaintCount"] = db.query(Complaint).filter(
        Complaint.station_id == s.id,
        Complaint.last_updated_snapshot == last_upd
    ).count()
    d["complaintThreshold"] = int(get_setting(db, "complaint_threshold", "5"))
    return d

# ══════════════════════════════════════════
# РОУТЫ: АВТОРИЗАЦИЯ
# ══════════════════════════════════════════

@app.post("/auth/register")
def register(data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.phone == data.phone).first():
        raise HTTPException(status_code=400, detail="Телефон уже зарегистрирован")
    user = User(
        name=data.name,
        phone=data.phone,
        password_hash=hash_password(data.password),
        station_id=data.station_id,
        telegram_id=data.telegram_id,
        is_approved=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"status": "pending", "message": "Заявка отправлена, ожидайте одобрения"}

@app.post("/auth/login")
async def login(data: dict, db: Session = Depends(get_db)):
    phone = data.get("username") or data.get("phone")
    password = data.get("password")
    user = db.query(User).filter(User.phone == phone).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if not user.is_approved and user.role != "admin":
        raise HTTPException(status_code=403, detail="Аккаунт не одобрен")
    return {"access_token": create_token(user.id), "token_type": "bearer"}

@app.get("/auth/me")
def me(authorization: str = None, db: Session = Depends(get_db)):
    # Принимаем токен из заголовка
    from fastapi import Request
    pass

# Переопределяем с Request
from fastapi import Request

@app.get("/auth/me")
async def get_me(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,
        "station_id": user.station_id,
        "telegram_id": user.telegram_id,
        "is_approved": user.is_approved,
    }

# ══════════════════════════════════════════
# РОУТЫ: УПРАВЛЕНИЕ СТАНЦИЕЙ (владелец)
# ══════════════════════════════════════════

@app.post("/stations/{station_id}/update")
async def update_station_status(station_id: int, data: StatusUpdate, request: Request, db: Session = Depends(get_db)):
    """Обновить статус газа — владелец или доверенный пользователь"""
    auth = request.headers.get("Authorization", "")

    # Проверяем: это авторизованный владелец?
    is_trusted = False
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    if auth.startswith("Bearer "):
        token = auth[7:]
        user = get_current_user(token, db)
        if user.station_id != station_id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Нет доступа")
    elif auth.startswith("Trusted "):
        # Доверенный пользователь передаёт свой telegram_id
        tg_id = auth[8:]
        trusted = db.query(TrustedUser).filter(
            TrustedUser.station_id == station_id,
            TrustedUser.telegram_id == tg_id
        ).first()
        if not trusted:
            raise HTTPException(status_code=403, detail="Нет доступа")
        is_trusted = True
    else:
        raise HTTPException(status_code=401, detail="Авторизация не передана")

    old_status = get_station_status(station)
    station.status = data.status
    station.last_updated = datetime.utcnow()  # Сброс жалоб: все старые привязаны к предыдущему last_updated
    db.commit()

    # Уведомляем подписчиков если газ появился
    if data.status == "green" and old_status != "green":
        subs = db.query(Subscription).filter(Subscription.station_id == station_id).all()
        status_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}
        for sub in subs:
            asyncio.create_task(send_tg(
                sub.telegram_id,
                f"🟢 *Газ появился!*\n📍 {station.name}\n\nСпешите — статус обновлён только что!"
            ))

    return {"status": "ok", "new_status": data.status}

@app.post("/stations/{station_id}/queue")
async def update_queue(station_id: int, data: QueueUpdate, request: Request, db: Session = Depends(get_db)):
    """Обновить уровень очереди (0-100)"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    # Проверка доступа: владелец или доверенный
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        user = get_current_user(auth[7:], db)
        if user.station_id != station_id and user.role != "admin":
            raise HTTPException(status_code=403)
    elif auth.startswith("Trusted "):
        tg_id = auth[8:]
        trusted = db.query(TrustedUser).filter(
            TrustedUser.station_id == station_id,
            TrustedUser.telegram_id == tg_id
        ).first()
        if not trusted:
            raise HTTPException(status_code=403)
    else:
        raise HTTPException(status_code=401)

    station.queue_level = max(0, min(100, data.queue_level))
    db.commit()
    return {"status": "ok", "queue_level": station.queue_level}

@app.post("/stations/{station_id}/services")
async def update_services(station_id: int, data: ServicesUpdate, request: Request, db: Session = Depends(get_db)):
    """Обновить список доп услуг (только владелец)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    station = db.query(Station).filter(Station.id == station_id).first()
    valid = {"wash", "air", "shop", "cafe", "tire", "vacuum"}
    station.services = [s for s in data.services if s in valid]
    db.commit()
    return {"status": "ok", "services": station.services}

@app.post("/stations/{station_id}/reminder")
async def update_reminder(station_id: int, data: ReminderUpdate, request: Request, db: Session = Depends(get_db)):
    """Настроить интервал напоминания (только владелец)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    station = db.query(Station).filter(Station.id == station_id).first()
    allowed = [30, 60, 120, 240, 480]
    if data.reminder_min not in allowed:
        raise HTTPException(status_code=400, detail=f"Допустимые значения: {allowed}")
    station.reminder_min = data.reminder_min
    db.commit()
    return {"status": "ok", "reminder_min": station.reminder_min}

@app.post("/stations/{station_id}/photos")
async def upload_photo(station_id: int, file: UploadFile = File(...), request: Request = None, db: Session = Depends(get_db)):
    """Загрузить фото станции (до 5 штук, только владелец)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    station = db.query(Station).filter(Station.id == station_id).first()
    photos = station.photos or []
    if len(photos) >= 5:
        raise HTTPException(status_code=400, detail="Максимум 5 фотографий")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(status_code=400, detail="Только jpg/png/webp")

    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    photo_url = f"/uploads/photos/{filename}"
    photos.append(photo_url)
    station.photos = photos
    db.commit()
    return {"status": "ok", "url": photo_url, "photos": photos}

@app.delete("/stations/{station_id}/photos")
async def delete_photo(station_id: int, url: str, request: Request, db: Session = Depends(get_db)):
    """Удалить фото"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    station = db.query(Station).filter(Station.id == station_id).first()
    photos = station.photos or []
    if url in photos:
        photos.remove(url)
        station.photos = photos
        db.commit()
        # Удаляем файл
        try:
            os.remove(url.lstrip("/"))
        except Exception:
            pass
    return {"status": "ok", "photos": photos}

# ══════════════════════════════════════════
# РОУТЫ: ДОВЕРЕННЫЕ ПОЛЬЗОВАТЕЛИ
# ══════════════════════════════════════════

@app.get("/stations/{station_id}/trusted")
async def get_trusted(station_id: int, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    trusted = db.query(TrustedUser).filter(TrustedUser.station_id == station_id).all()
    return [{"id": t.id, "telegram_id": t.telegram_id, "name": t.name, "added_at": t.added_at.isoformat()} for t in trusted]

@app.post("/stations/{station_id}/trusted")
async def add_trusted(station_id: int, data: TrustedUserAdd, request: Request, db: Session = Depends(get_db)):
    """Добавить доверенного пользователя (максимум 3)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    existing = db.query(TrustedUser).filter(TrustedUser.station_id == station_id).count()
    if existing >= 3:
        raise HTTPException(status_code=400, detail="Максимум 3 доверенных пользователя")

    duplicate = db.query(TrustedUser).filter(
        TrustedUser.station_id == station_id,
        TrustedUser.telegram_id == data.telegram_id
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Уже добавлен")

    trusted = TrustedUser(
        station_id=station_id,
        telegram_id=data.telegram_id,
        name=data.name,
        added_by=user.id,
    )
    db.add(trusted)
    db.commit()
    db.refresh(trusted)

    # Уведомляем доверенного пользователя в Telegram
    asyncio.create_task(send_tg(
        data.telegram_id,
        f"✅ *Вас добавили как доверенного!*\n\n"
        f"📍 Станция: *{db.query(Station).filter(Station.id == station_id).first().name}*\n"
        f"👤 Добавил: {user.name}\n\n"
        f"Теперь вы можете обновлять статус газа и очереди через бота."
    ))

    return {"status": "ok", "id": trusted.id}

@app.delete("/stations/{station_id}/trusted/{trusted_id}")
async def remove_trusted(station_id: int, trusted_id: int, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.station_id != station_id and user.role != "admin":
        raise HTTPException(status_code=403)

    trusted = db.query(TrustedUser).filter(
        TrustedUser.id == trusted_id,
        TrustedUser.station_id == station_id
    ).first()
    if not trusted:
        raise HTTPException(status_code=404)
    db.delete(trusted)
    db.commit()
    return {"status": "ok"}

# ══════════════════════════════════════════
# РОУТЫ: ЖАЛОБЫ
# ══════════════════════════════════════════

class ComplaintRequest(BaseModel):
    telegram_id: Optional[str] = None

@app.post("/stations/{station_id}/complaint")
async def file_complaint(station_id: int, data: ComplaintRequest, db: Session = Depends(get_db)):
    """Пожаловаться. 1 раз в 24ч на станцию. Жалобы сбрасываются при обновлении статуса."""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    threshold = int(get_setting(db, "complaint_threshold", "5"))
    last_upd = station.last_updated.isoformat() if station.last_updated else ""

    # Проверка 24ч лимита по telegram_id
    if data.telegram_id:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = db.query(Complaint).filter(
            Complaint.station_id == station_id,
            Complaint.telegram_id == data.telegram_id,
            Complaint.created_at >= cutoff
        ).first()
        if recent:
            hours_left = int(24 - (datetime.utcnow() - recent.created_at).total_seconds() / 3600)
            raise HTTPException(status_code=400, detail=f"Повторная жалоба через {hours_left} ч")

    complaint = Complaint(
        station_id=station_id,
        telegram_id=data.telegram_id,
        last_updated_snapshot=last_upd,
    )
    db.add(complaint)
    db.commit()

    # Считаем жалобы только для текущего last_updated (после сброса — обнуляются)
    count = db.query(Complaint).filter(
        Complaint.station_id == station_id,
        Complaint.last_updated_snapshot == last_upd
    ).count()

    status_changed = False
    if count >= threshold and station.status != "purple":
        station.status = "purple"
        db.commit()
        status_changed = True
        owner = db.query(User).filter(User.id == station.owner_id).first() if station.owner_id else None
        if owner and owner.telegram_id:
            asyncio.create_task(send_tg(
                owner.telegram_id,
                f"⚠️ *Статус станции изменён!*\n\n"
                f"📍 {station.name}\n"
                f"Водители сообщают о несоответствии статуса.\n"
                f"Жалоб: *{count}* из {threshold}\n\n"
                f"Обновите статус в личном кабинете."
            ))

    return {
        "status": "ok",
        "complaint_count": count,
        "threshold": threshold,
        "status_changed": status_changed,
        "new_status": station.status
    }

@app.get("/stations/{station_id}/complaints")
async def get_complaints(station_id: int, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    threshold = int(get_setting(db, "complaint_threshold", "5"))
    last_upd = station.last_updated.isoformat() if station.last_updated else ""
    count = db.query(Complaint).filter(
        Complaint.station_id == station_id,
        Complaint.last_updated_snapshot == last_upd
    ).count()
    return {"complaint_count": count, "threshold": threshold}


# ══════════════════════════════════════════
# РОУТЫ: ПОДПИСКИ
# ══════════════════════════════════════════

@app.post("/subscribe")
def subscribe(data: SubscribeRequest, db: Session = Depends(get_db)):
    existing = db.query(Subscription).filter(
        Subscription.telegram_id == data.telegram_id,
        Subscription.station_id == data.station_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"subscribed": False}
    sub = Subscription(telegram_id=data.telegram_id, station_id=data.station_id)
    db.add(sub)
    db.commit()
    return {"subscribed": True}

@app.get("/subscribe/check")
def check_subscription(telegram_id: str, station_id: int, db: Session = Depends(get_db)):
    exists = db.query(Subscription).filter(
        Subscription.telegram_id == telegram_id,
        Subscription.station_id == station_id
    ).first()
    return {"subscribed": bool(exists)}

# ══════════════════════════════════════════
# РОУТЫ: АДМИН
# ══════════════════════════════════════════

@app.get("/admin/users")
async def admin_get_users(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    if user.role != "admin":
        raise HTTPException(status_code=403)
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name, "phone": u.phone, "role": u.role,
             "is_approved": u.is_approved, "station_id": u.station_id} for u in users]

@app.post("/admin/users/{user_id}/approve")
async def admin_approve(user_id: int, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    user.is_approved = True
    db.commit()
    if user.telegram_id:
        asyncio.create_task(send_tg(
            user.telegram_id,
            f"✅ *Ваша заявка одобрена!*\n\nТеперь вы можете управлять станцией через личный кабинет."
        ))
    return {"status": "ok"}

@app.post("/admin/stations")
async def admin_create_station(data: StationCreate, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    station = Station(name=data.name, lat=data.lat, lon=data.lon, description=data.description)
    db.add(station)
    db.commit()
    db.refresh(station)
    return station_to_dict(station)

@app.get("/admin/settings")
async def admin_get_settings(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    return {
        "complaint_threshold": get_setting(db, "complaint_threshold", "5"),
    }

@app.post("/admin/settings")
async def admin_update_settings(data: dict, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    if "complaint_threshold" in data:
        val = int(data["complaint_threshold"])
        if not 1 <= val <= 100:
            raise HTTPException(status_code=400, detail="Порог должен быть от 1 до 100")
        set_setting(db, "complaint_threshold", str(val))
    return {"status": "ok"}

@app.get("/admin/complaints")
async def admin_get_complaints(request: Request, db: Session = Depends(get_db)):
    """Все станции с жалобами"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    threshold = int(get_setting(db, "complaint_threshold", "5"))
    stations = db.query(Station).all()
    result = []
    for s in stations:
        last_upd = s.last_updated.isoformat() if s.last_updated else ""
        count = db.query(Complaint).filter(
            Complaint.station_id == s.id,
            Complaint.last_updated_snapshot == last_upd
        ).count()
        if count > 0:
            result.append({
                "station_id": s.id,
                "station_name": s.name,
                "status": s.status,
                "complaint_count": count,
                "threshold": threshold,
            })
    return sorted(result, key=lambda x: x["complaint_count"], reverse=True)

@app.post("/admin/complaints/{station_id}/reset")
async def admin_reset_complaints(station_id: int, request: Request, db: Session = Depends(get_db)):
    """Сбросить жалобы вручную (без смены статуса)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    # Сдвигаем last_updated чтобы старые жалобы не считались
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    station.last_updated = datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@app.post("/admin/premium/{station_id}")
async def admin_set_premium(station_id: int, days: int = 30, request: Request = None, db: Session = Depends(get_db)):
    """Выдать премиум станции"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    station.is_premium = True
    station.premium_until = datetime.utcnow() + timedelta(days=days)
    db.commit()
    return {"status": "ok", "premium_until": station.premium_until.isoformat()}

# ══════════════════════════════════════════
# ФОНОВАЯ ЗАДАЧА: НАПОМИНАНИЯ
# ══════════════════════════════════════════

async def reminder_worker():
    """Каждые 10 минут проверяем — нужно ли слать напоминание владельцу обновить статус"""
    while True:
        await asyncio.sleep(600)  # 10 минут
        try:
            db = SessionLocal()
            stations = db.query(Station).filter(Station.owner_id != None).all()
            for s in stations:
                owner = db.query(User).filter(User.id == s.owner_id).first()
                if not owner or not owner.telegram_id:
                    continue
                minutes_since = (datetime.utcnow() - s.last_updated).total_seconds() / 60
                if minutes_since >= s.reminder_min:
                    # Проверяем, не отправляли ли уже
                    last_reminder = db.query(ReminderLog).filter(
                        ReminderLog.station_id == s.id
                    ).order_by(ReminderLog.sent_at.desc()).first()
                    if last_reminder:
                        since_last = (datetime.utcnow() - last_reminder.sent_at).total_seconds() / 60
                        if since_last < s.reminder_min:
                            continue
                    # Отправляем
                    await send_tg(owner.telegram_id,
                        f"⏰ *Напоминание*\n\n"
                        f"📍 {s.name}\n"
                        f"Не забудьте обновить статус газа\!\n"
                        f"Последнее обновление: {int(minutes_since)} мин назад"
                    )
                    log = ReminderLog(station_id=s.id)
                    db.add(log)
                    db.commit()
            db.close()
        except Exception as e:
            print(f"Reminder error: {e}")

@app.on_event("startup")
async def startup():
    asyncio.create_task(reminder_worker())

# Статические файлы
try:
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception:
    pass

# ══════════════════════════════════════════
# SEED: admin пользователь
# ══════════════════════════════════════════
def seed():
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.phone == "admin").first():
            admin = User(
                name="Admin",
                phone="admin",
                password_hash=hash_password("admin123"),
                role="admin",
                is_approved=True,
            )
            db.add(admin)
        if not db.query(Station).first():
            for s in [
                Station(name="АГЗС Мкр 2", lat=43.6520, lon=51.1580, status="green"),
                Station(name="АГЗС Мкр 5", lat=43.6612, lon=51.1743, status="yellow"),
                Station(name="АГЗС Промзона", lat=43.6401, lon=51.2012, status="red"),
            ]:
                db.add(s)
        db.commit()
    finally:
        db.close()

seed()