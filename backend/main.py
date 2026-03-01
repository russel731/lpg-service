from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, BigInteger, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lpguser:lpgpass@127.0.0.1:5432/lpgdb")
SECRET_KEY = "lpg-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
BOT_TOKEN = os.getenv("BOT_TOKEN", "8482373207:AAGmeRGPBpiikO5mzxWuTJcVxsKDTTVc1CY")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class Station(Base):
    __tablename__ = "stations"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    status = Column(String, default="purple")
    last_updated = Column(DateTime, default=datetime.utcnow)
    owner_id = Column(Integer, nullable=True)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="owner")
    is_approved = Column(Boolean, default=False)
    station_id = Column(Integer, nullable=True)
    telegram_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, nullable=False)
    station_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('telegram_id', 'station_id', name='uq_sub'),)

Base.metadata.create_all(bind=engine)

# Миграции
try:
    with engine.connect() as conn:
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT")
        conn.commit()
except:
    pass

def seed():
    db = SessionLocal()
    if db.query(Station).count() == 0:
        db.add_all([
            Station(name="Газ Актау 1", lat=43.65, lon=51.16, status="green", last_updated=datetime.utcnow()),
            Station(name="Газ Актау 2", lat=43.66, lon=51.14, status="yellow", last_updated=datetime.utcnow()),
            Station(name="Газ Актау 3", lat=43.67, lon=51.15, status="red", last_updated=datetime.utcnow()),
        ])
        db.commit()
    existing_admin = db.query(User).filter(User.phone == "admin").first()
    if existing_admin:
        db.delete(existing_admin)
        db.commit()
    admin = User(name="Admin", phone="admin", password_hash=pwd_context.hash("admin123"), role="admin", is_approved=True)
    db.add(admin)
    db.commit()
    db.close()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/miniapp")
def miniapp():
    return FileResponse("static/miniapp.html")

@app.get("/admin")
def admin_page():
    return FileResponse("static/admin.html")

@app.on_event("startup")
def startup():
    seed()

def create_token(data: dict):
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    db = SessionLocal()
    user = db.query(User).filter(User.id == int(user_id)).first()
    db.close()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user

async def send_telegram_message(telegram_id: int, text: str):
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={"chat_id": telegram_id, "text": text, "parse_mode": "Markdown"}
            )
    except Exception as e:
        print(f"Telegram notify error: {e}")

class RegisterSchema(BaseModel):
    name: str
    phone: str
    password: str
    station_id: int
    telegram_id: int | None = None

class StationCreate(BaseModel):
    name: str
    lat: float
    lon: float
    status: str = "purple"

class StationUpdate(BaseModel):
    status: str

class SubscribeSchema(BaseModel):
    telegram_id: int
    station_id: int

@app.post("/auth/register")
def register(data: RegisterSchema):
    db = SessionLocal()
    if db.query(User).filter(User.phone == data.phone).first():
        db.close()
        raise HTTPException(status_code=400, detail="Номер уже зарегистрирован")
    station = db.query(Station).filter(Station.id == data.station_id).first()
    if not station:
        db.close()
        raise HTTPException(status_code=404, detail="Станция не найдена")
    user = User(name=data.name, phone=data.phone, password_hash=pwd_context.hash(data.password), station_id=data.station_id, telegram_id=data.telegram_id, is_approved=False)
    db.add(user)
    db.commit()
    db.close()
    return {"message": "Заявка отправлена на модерацию"}

@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.phone == form.username).first()
    db.close()
    if not user or not pwd_context.verify(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if not user.is_approved:
        raise HTTPException(status_code=403, detail="Аккаунт ещё не одобрен")
    token = create_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer", "role": user.role}

@app.get("/auth/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "name": user.name, "phone": user.phone, "role": user.role, "is_approved": user.is_approved, "station_id": user.station_id}

# ═══ ПОДПИСКИ ═══
@app.post("/subscribe")
def subscribe(data: SubscribeSchema):
    db = SessionLocal()
    existing = db.query(Subscription).filter(
        Subscription.telegram_id == data.telegram_id,
        Subscription.station_id == data.station_id
    ).first()
    if existing:
        db.delete(existing)
        db.commit()
        db.close()
        return {"subscribed": False, "message": "Подписка отменена"}
    sub = Subscription(telegram_id=data.telegram_id, station_id=data.station_id)
    db.add(sub)
    db.commit()
    db.close()
    return {"subscribed": True, "message": "Подписка оформлена"}

@app.get("/subscribe/check")
def check_subscription(telegram_id: int, station_id: int):
    db = SessionLocal()
    exists = db.query(Subscription).filter(
        Subscription.telegram_id == telegram_id,
        Subscription.station_id == station_id
    ).first()
    db.close()
    return {"subscribed": bool(exists)}

@app.get("/admin/users")
def get_users(admin: User = Depends(get_admin)):
    db = SessionLocal()
    users = db.query(User).filter(User.role != "admin").all()
    stations = db.query(Station).all()
    station_map = {s.id: s.name for s in stations}
    db.close()
    return [{"id": u.id, "name": u.name, "phone": u.phone, "is_approved": u.is_approved, "station_id": u.station_id, "station_name": station_map.get(u.station_id, "—"), "telegram_id": u.telegram_id, "created_at": u.created_at.isoformat()} for u in users]

@app.post("/admin/users/{user_id}/approve")
async def approve_user(user_id: int, admin: User = Depends(get_admin)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    station_name = "—"
    if user.station_id:
        station = db.query(Station).filter(Station.id == user.station_id).first()
        if station:
            station.owner_id = user.id
            station_name = station.name
    telegram_id = user.telegram_id
    db.commit()
    db.close()
    if telegram_id:
        await send_telegram_message(telegram_id, f"✅ *Ваша заявка одобрена!*\n\n📍 Станция: *{station_name}*\n\nТеперь вы можете войти в приложение и управлять статусом станции.")
    return {"message": "Пользователь одобрен"}

@app.post("/admin/users/{user_id}/reject")
async def reject_user(user_id: int, admin: User = Depends(get_admin)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    telegram_id = user.telegram_id
    db.delete(user)
    db.commit()
    db.close()
    if telegram_id:
        await send_telegram_message(telegram_id, "❌ *Ваша заявка отклонена*\n\nК сожалению, ваша заявка на регистрацию была отклонена администратором.")
    return {"message": "Пользователь отклонён"}

@app.get("/stations")
def get_stations():
    db = SessionLocal()
    stations = db.query(Station).all()
    result = []
    for s in stations:
        status = s.status
        if datetime.utcnow() - s.last_updated > timedelta(hours=24):
            status = "purple"
        result.append({"id": s.id, "name": s.name, "lat": s.lat, "lon": s.lon, "status": status, "lastUpdated": s.last_updated.isoformat(), "hasOwner": s.owner_id is not None})
    db.close()
    return result

@app.post("/stations")
def create_station(data: StationCreate, user: User = Depends(get_admin)):
    db = SessionLocal()
    station = Station(name=data.name, lat=data.lat, lon=data.lon, status=data.status, last_updated=datetime.utcnow())
    db.add(station)
    db.commit()
    db.refresh(station)
    db.close()
    return {"id": station.id, "name": station.name, "lat": station.lat, "lon": station.lon, "status": station.status}

@app.put("/admin/stations/{station_id}")
def edit_station(station_id: int, data: StationCreate, admin: User = Depends(get_admin)):
    db = SessionLocal()
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        db.close()
        raise HTTPException(status_code=404, detail="Station not found")
    station.name = data.name
    station.lat = data.lat
    station.lon = data.lon
    station.status = data.status
    db.commit()
    db.close()
    return {"message": "Станция обновлена"}

@app.delete("/admin/stations/{station_id}")
def delete_station(station_id: int, admin: User = Depends(get_admin)):
    db = SessionLocal()
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        db.close()
        raise HTTPException(status_code=404, detail="Station not found")
    db.delete(station)
    db.commit()
    db.close()
    return {"message": "Станция удалена"}

@app.post("/stations/{station_id}/update")
async def update_station(station_id: int, data: StationUpdate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        db.close()
        raise HTTPException(status_code=404, detail="Station not found")
    if user.role != "admin" and station.owner_id != user.id:
        db.close()
        raise HTTPException(status_code=403, detail="Нет доступа")

    old_status = station.status
    station.status = data.status
    station.last_updated = datetime.utcnow()
    station_name = station.name
    station_lat = station.lat
    station_lon = station.lon

    # Уведомляем подписчиков если статус стал green
    subs = []
    if data.status == "green" and old_status != "green":
        subs = db.query(Subscription).filter(Subscription.station_id == station_id).all()

    db.commit()
    db.close()

    if subs:
        maps_url = f"https://maps.google.com/maps?q={station_lat},{station_lon}"
        text = (
            f"⛽ *Газ появился!*\n\n"
            f"📍 *{station_name}*\n"
            f"🟢 Газ есть — езжайте скорее!\n\n"
            f"🗺 [Открыть на карте]({maps_url})"
        )
        for sub in subs:
            await send_telegram_message(sub.telegram_id, text)

    return {"success": True}

@app.get("/admin/stats")
def get_stats(admin: User = Depends(get_admin)):
    db = SessionLocal()
    stations = db.query(Station).all()
    users = db.query(User).filter(User.role != "admin").all()
    db.close()
    return {
        "total_stations": len(stations),
        "by_status": {"green": len([s for s in stations if s.status == "green"]), "yellow": len([s for s in stations if s.status == "yellow"]), "red": len([s for s in stations if s.status == "red"]), "purple": len([s for s in stations if s.status == "purple"])},
        "total_users": len(users),
        "pending_users": len([u for u in users if not u.is_approved]),
        "approved_users": len([u for u in users if u.is_approved]),
    }