from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://lpguser:lpgpass@localhost:5432/lpgdb")
SECRET_KEY = "lpg-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# ======================
# Модели БД
# ======================
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
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# ======================
# Seed
# ======================
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
    admin = User(
        name="Admin",
        phone="admin",
        password_hash=pwd_context.hash("admin123"),
        role="admin",
        is_approved=True,
    )
    db.add(admin)
    db.commit()
    db.close()

# ======================
# FastAPI
# ======================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    seed()

# ======================
# Auth helpers
# ======================
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

# ======================
# Schemas
# ======================
class RegisterSchema(BaseModel):
    name: str
    phone: str
    password: str
    station_id: int

class StationCreate(BaseModel):
    name: str
    lat: float
    lon: float
    status: str = "purple"

class StationUpdate(BaseModel):
    status: str

# ======================
# Auth endpoints
# ======================
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
    user = User(
        name=data.name,
        phone=data.phone,
        password_hash=pwd_context.hash(data.password),
        station_id=data.station_id,
        is_approved=False,
    )
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
    return {
        "id": user.id,
        "name": user.name,
        "phone": user.phone,
        "role": user.role,
        "is_approved": user.is_approved,
        "station_id": user.station_id,
    }

# ======================
# Admin endpoints
# ======================
@app.get("/admin/users")
def get_users(admin: User = Depends(get_admin)):
    db = SessionLocal()
    users = db.query(User).filter(User.role != "admin").all()
    db.close()
    return [{"id": u.id, "name": u.name, "phone": u.phone,
             "is_approved": u.is_approved, "station_id": u.station_id,
             "created_at": u.created_at.isoformat()} for u in users]

@app.post("/admin/users/{user_id}/approve")
def approve_user(user_id: int, admin: User = Depends(get_admin)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    user.is_approved = True
    if user.station_id:
        station = db.query(Station).filter(Station.id == user.station_id).first()
        if station:
            station.owner_id = user.id
    db.commit()
    db.close()
    return {"message": "Пользователь одобрен"}

@app.post("/admin/users/{user_id}/reject")
def reject_user(user_id: int, admin: User = Depends(get_admin)):
    db = SessionLocal()
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.close()
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    db.close()
    return {"message": "Пользователь отклонён"}

# ======================
# Station endpoints
# ======================
@app.get("/stations")
def get_stations():
    db = SessionLocal()
    stations = db.query(Station).all()
    result = []
    for s in stations:
        status = s.status
        if datetime.utcnow() - s.last_updated > timedelta(hours=24):
            status = "purple"
        result.append({
            "id": s.id,
            "name": s.name,
            "lat": s.lat,
            "lon": s.lon,
            "status": status,
            "lastUpdated": s.last_updated.isoformat(),
            "hasOwner": s.owner_id is not None,
        })
    db.close()
    return result

@app.post("/stations")
def create_station(data: StationCreate, user: User = Depends(get_admin)):
    db = SessionLocal()
    station = Station(
        name=data.name,
        lat=data.lat,
        lon=data.lon,
        status=data.status,
        last_updated=datetime.utcnow()
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    db.close()
    return {"id": station.id, "name": station.name,
            "lat": station.lat, "lon": station.lon, "status": station.status}

@app.post("/stations/{station_id}/update")
def update_station(station_id: int, data: StationUpdate, user: User = Depends(get_current_user)):
    db = SessionLocal()
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        db.close()
        raise HTTPException(status_code=404, detail="Station not found")
    if user.role != "admin" and station.owner_id != user.id:
        db.close()
        raise HTTPException(status_code=403, detail="Нет доступа")
    station.status = data.status
    station.last_updated = datetime.utcnow()
    db.commit()
    db.close()
    return {"success": True}