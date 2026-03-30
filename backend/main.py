from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.orm.attributes import flag_modified
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
from jose import jwt
import bcrypt, httpx, asyncio, os, json, shutil, uuid

# ══════════════════════════════════════════
# TELEGRAM УВЕДОМЛЕНИЯ
# ══════════════════════════════════════════

async def send_telegram_notification(telegram_id: str, text: str, bot_token: str = None) -> bool:
    """Отправить уведомление через Telegram Bot API"""
    token = bot_token or os.getenv("BOT_TOKEN", "8482373207:AAGmeRGPBpiikO5mzxWuTJcVxsKDTTVc1CY")
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json={
                "chat_id": telegram_id,
                "text": text,
                "parse_mode": "Markdown"
            }, timeout=10.0)
            return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки уведомления: {e}")
        return False

# ══════════════════════════════════════════
# КОНФИГ
# ══════════════════════════════════════════
DATABASE_URL = os.getenv("DATABASE_URL","sqlite:///./lpg.db")
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
    status        = Column(String, default="green")
    last_updated  = Column(DateTime, default=datetime.utcnow)
    owner_id      = Column(Integer, ForeignKey("users.id"), nullable=True)
    working_hours = Column(JSON, default=None)
    queue_level   = Column(Integer, default=0)
    services      = Column(JSON, default=list)
    photos        = Column(JSON, default=list)
    reminder_min  = Column(Integer, default=120)
    is_premium    = Column(Boolean, default=False)
    premium_until = Column(DateTime, nullable=True)
    description   = Column(Text, nullable=True)
    phone         = Column(String, nullable=True)
    gas_price     = Column(Float, nullable=True)
    
    # Новые поля для системы жалоб
    complaints_count      = Column(Integer, default=0)
    last_complaint_reset  = Column(DateTime, default=datetime.utcnow)

    owner         = relationship("User", back_populates="station", foreign_keys=[owner_id])
    trusted_users = relationship("TrustedUser", back_populates="station")
    subscriptions = relationship("Subscription", back_populates="station")


class User(Base):
    __tablename__ = "users"
    id            = Column(Integer, primary_key=True)
    name          = Column(String, nullable=False)
    phone         = Column(String, nullable=False, unique=True)
    password_hash = Column(String, nullable=False)
    role          = Column(String, default="owner")
    is_approved   = Column(Boolean, default=False)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=True)
    telegram_id   = Column(String, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    station       = relationship("Station", back_populates="owner", foreign_keys=[Station.owner_id])


class TrustedUser(Base):
    __tablename__ = "trusted_users"
    id            = Column(Integer, primary_key=True)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=False)
    telegram_id   = Column(String, nullable=False)
    name          = Column(String, nullable=False)
    password_hash = Column(String, nullable=True)
    added_at      = Column(DateTime, default=datetime.utcnow)
    added_by      = Column(Integer, ForeignKey("users.id"))

    station       = relationship("Station", back_populates="trusted_users")


class Subscription(Base):
    __tablename__ = "subscriptions"
    id            = Column(Integer, primary_key=True)
    telegram_id   = Column(String, nullable=False)
    station_id    = Column(Integer, ForeignKey("stations.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    station       = relationship("Station", back_populates="subscriptions")


class ReminderLog(Base):
    __tablename__ = "reminder_logs"
    id            = Column(Integer, primary_key=True)
    station_id    = Column(Integer, nullable=False)
    sent_at       = Column(DateTime, default=datetime.utcnow)


class Complaint(Base):
    __tablename__ = "complaints"
    id                    = Column(Integer, primary_key=True)
    station_id            = Column(Integer, ForeignKey("stations.id"), nullable=False)
    user_telegram_id      = Column(String, nullable=False)
    reason                = Column(String, nullable=False)  # "no_gas", "low_gas", "closed", "wrong_price", "other"
    comment               = Column(Text, nullable=True)
    photo_url             = Column(String, nullable=True)
    created_at            = Column(DateTime, default=datetime.utcnow)
    
    # Старые поля для совместимости
    telegram_id           = Column(String, nullable=True)
    status_snapshot       = Column(String, nullable=True)
    last_updated_snapshot = Column(String, nullable=True)


class Settings(Base):
    __tablename__ = "settings"
    key   = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class Feedback(Base):
    __tablename__ = "feedback"
    id         = Column(Integer, primary_key=True)
    category   = Column(String, nullable=False)
    text       = Column(String, nullable=False)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=True)
    telegram_id = Column(String, nullable=True)
    lang       = Column(String, default="ru")
    created_at = Column(DateTime, default=datetime.utcnow)

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

class StatusUpdate(BaseModel):
    status: str

class QueueUpdate(BaseModel):
    queue_level: int

class ServicesUpdate(BaseModel):
    services: List[str]

class ReminderUpdate(BaseModel):
    reminder_min: int

class TrustedUserAdd(BaseModel):
    telegram_id: str
    name: str
    password: Optional[str] = None

class StationCreate(BaseModel):
    name: str
    lat: float
    lon: float
    description: Optional[str] = None
    phone: Optional[str] = None

class SubscribeRequest(BaseModel):
    telegram_id: str
    station_id: int

class WorkingHoursRequest(BaseModel):
    working_hours: dict

class FeedbackRequest(BaseModel):
    category: str
    text: str
    station_id: Optional[int] = None
    telegram_id: Optional[str] = None
    lang: Optional[str] = "ru"
    username: Optional[str] = None

class ComplaintRequest(BaseModel):
    telegram_id: Optional[str] = None

class TgAuthRequest(BaseModel):
    telegram_id: str
class GasPriceUpdate(BaseModel):
    gas_price: float

class ComplaintCreate(BaseModel):
    user_telegram_id: str
    reason: str  # "no_gas", "low_gas", "closed", "wrong_price", "other"
    comment: Optional[str] = None
    photo_url: Optional[str] = None

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
        "queueLevel": s.queue_level,
        "gasPrice": s.gas_price if hasattr(s, 'gas_price') else None,
        "services": s.services or [],
        "workingHours": s.working_hours,
        "photos": s.photos or [],
        "isPremium": s.is_premium,
        "description": s.description,
        "phone": s.phone if hasattr(s, 'phone') else None,
        "complaintCount": s.complaint_count if hasattr(s, 'complaint_count') else 0,
    }

async def send_tg(chat_id: str, text: str):
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        )

def get_token_from_header(authorization: str) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не передан")
    return authorization[7:]

# ══════════════════════════════════════════
# РОУТЫ
# ══════════════════════════════════════════

from fastapi import Request

from pathlib import Path

import httpx as _httpx

# Кэш для Leaflet JS/CSS — скачиваем один раз при первом запросе
_leaflet_cache = {"js": None, "css": None}

async def _get_leaflet():
    """Скачать и закэшировать Leaflet JS и CSS для инлайна"""
    if _leaflet_cache["js"] is None:
        print("📦 Downloading Leaflet for inline...")
        async with _httpx.AsyncClient(timeout=30.0) as client:
            js_r = await client.get("https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js")
            css_r = await client.get("https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css")
            _leaflet_cache["js"] = js_r.text
            _leaflet_cache["css"] = css_r.text
        print(f"✅ Leaflet cached: JS={len(_leaflet_cache['js'])}b, CSS={len(_leaflet_cache['css'])}b")
    return _leaflet_cache["js"], _leaflet_cache["css"]

@app.get("/")
async def serve_index():
    file_path = Path(__file__).parent.parent / "frontend" / "public" / "index.html"
    if not file_path.exists():
        return {"message": "АГЗС Мониторинг API"}
    return FileResponse(str(file_path))

@app.get("/miniapp")
async def serve_miniapp(request: Request, skip: str = None, lang: str = None):
    print(f"📱 /miniapp called: skip={skip}, lang={lang}")
    file_path = Path(__file__).parent.parent / "frontend" / "public" / "miniapp.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="miniapp.html not found")
    
    html = file_path.read_text(encoding="utf-8")
    
    if skip == "1":
        # Для кнопки бота: Telegram загружает через srcdoc, внешние скрипты блокируются
        # Инлайним Leaflet JS/CSS прямо в HTML
        try:
            leaflet_js, leaflet_css = await _get_leaflet()
            # Заменяем внешние ссылки на инлайн
            html = html.replace(
                '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>',
                f'<style>{leaflet_css}</style>'
            )
            html = html.replace(
                '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>',
                f'<script>{leaflet_js}</script>'
            )
            # Также заменяем Telegram SDK (тоже блокируется в srcdoc)
            html = html.replace(
                '<script src="https://telegram.org/js/telegram-web-app.js"></script>',
                '<!-- telegram SDK unavailable in srcdoc -->'
            )
            # Скрываем welcome, вызываем enterAs
            inject = '<style id="skip-inject">#welcome-screen{display:none!important}</style>\n'
            if lang in ("ru", "kz"):
                inject += f'<script>window.__LANG__="{lang}";</script>\n'
            html = html.replace('<body>', '<body>\n' + inject, 1)
            print("✅ Inlined Leaflet + skip CSS")
        except Exception as e:
            print(f"❌ Inline error: {e}")
            # Fallback — отдаём как есть
    elif lang in ("ru", "kz"):
        inject = f'<script>window.__LANG__="{lang}";</script>\n'
        html = html.replace('<body>', '<body>\n' + inject, 1)
    
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)

@app.get("/admin.html")
async def serve_admin():
    file_path = Path(__file__).parent.parent / "frontend" / "public" / "admin.html"
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="admin.html not found")
    return FileResponse(str(file_path))

@app.get("/miniapp_map")
async def serve_miniapp_map(lang: str = "ru"):
    """Полноценная карта для кнопки 'Открыть карту' — инлайн Leaflet для srcdoc iframe"""
    try:
        leaflet_js, leaflet_css = await _get_leaflet()
    except Exception as e:
        from fastapi.responses import HTMLResponse
        return HTMLResponse(f"<h1>Ошибка загрузки карты: {e}</h1>")
    
    kz = lang == 'kz'
    
    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>{leaflet_css}</style>
<script>{leaflet_js}</script>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;overflow:hidden}}
#map{{width:100%;height:100vh}}
.legend{{position:fixed;bottom:12px;left:12px;z-index:1000;background:rgba(255,255,255,0.85);backdrop-filter:blur(10px);border-radius:14px;padding:10px 14px;box-shadow:0 4px 20px rgba(0,0,0,0.08);font-size:12px}}
.legend-item{{display:flex;align-items:center;gap:6px;margin:4px 0}}
.legend-dot{{width:10px;height:10px;border-radius:50%;flex-shrink:0}}
.loc-btn{{position:fixed;bottom:12px;right:12px;z-index:1000;width:44px;height:44px;border-radius:12px;border:none;background:white;box-shadow:0 4px 16px rgba(0,0,0,0.12);font-size:20px;cursor:pointer}}
.leaflet-popup-content-wrapper{{border-radius:14px!important;box-shadow:0 8px 30px rgba(0,0,0,0.15)!important}}
.leaflet-popup-content{{margin:14px 16px!important;font-size:13px!important;line-height:1.4!important}}
</style>
</head><body>
<div id="map"></div>
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#22c55e"></div>{'Газ бар' if kz else 'Газ есть'}</div>
  <div class="legend-item"><div class="legend-dot" style="background:#eab308"></div>{'Газ аз' if kz else 'Газ мало'}</div>
  <div class="legend-item"><div class="legend-dot" style="background:#ef4444"></div>{'Газ жоқ' if kz else 'Газа нет'}</div>
  <div class="legend-item"><div class="legend-dot" style="background:#a855f7"></div>{'Белгісіз' if kz else 'Неизвестно'}</div>
</div>
<button class="loc-btn" onclick="locateMe()">📍</button>

<script>
var API = window.location.origin || '';
var H = {{'ngrok-skip-browser-warning':'true'}};
var colors = {{green:'#22c55e',yellow:'#eab308',red:'#ef4444',purple:'#a855f7'}};
var statusBg = {{green:'rgba(34,197,94,0.12)',yellow:'rgba(234,179,8,0.12)',red:'rgba(239,68,68,0.12)',purple:'rgba(168,85,247,0.12)'}};
var statusIco = {{green:'🟢',yellow:'🟡',red:'🔴',purple:'🟣'}};
var statusTxt = {{green:'{'Газ бар' if kz else 'Газ есть'}',yellow:'{'Газ аз' if kz else 'Газ мало'}',red:'{'Газ жоқ' if kz else 'Газа нет'}',purple:'{'Белгісіз' if kz else 'Неизвестно'}'}};
var svcNames = {{wash:'🚿 {'Жуу' if kz else 'Мойка'}',air:'💨 {'Ауа' if kz else 'Подкачка'}',shop:'🛒 {'Дүкен' if kz else 'Магазин'}',cafe:'☕ {'Кафе' if kz else 'Кафе'}',tire:'🔧 {'Шина' if kz else 'Шиномонтаж'}',vacuum:'🌀 {'Шаңсорғыш' if kz else 'Пылесос'}'}};
var map, userMarker, userLat, userLon;

try {{
  map = L.map('map', {{zoomControl:false}}).setView([43.6532, 51.1575], 13);
  L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{maxZoom:19}}).addTo(map);
  L.control.zoom({{position:'topright'}}).addTo(map);

  fetch(API+'/stations', {{headers:H}}).then(r=>r.json()).then(stations=>{{
    stations.forEach(s=>{{
      var c = colors[s.status] || '#a855f7';
      var icon = L.divIcon({{html:'<div style="width:36px;height:36px;border-radius:50% 50% 50% 0;background:'+c+';transform:rotate(-45deg);border:3px solid white;box-shadow:0 4px 12px rgba(0,0,0,0.2)"></div>',iconSize:[36,36],iconAnchor:[18,36],className:''}});
      
      var dist = (userLat && userLon) ? (calcDist(userLat,userLon,s.lat,s.lon).toFixed(1)+' km') : '';
      var ql = s.queueLevel || 0;
      var qTxt = '';
      if(s.hasOwner){{
        if(ql<=30) qTxt='<div style="font-size:11px;margin-top:4px;color:#22c55e">🚦 {'Бос' if kz else 'Свободно'}</div>';
        else if(ql<=60) qTxt='<div style="font-size:11px;margin-top:4px;color:#eab308">🚦 {'Орташа' if kz else 'Средняя'}</div>';
        else qTxt='<div style="font-size:11px;margin-top:4px;color:#ef4444">🚦 {'Кезек' if kz else 'Очередь'}</div>';
      }}
      
      var hTxt = '';
      if(s.workingHours) {{
        try {{
          var wh = s.workingHours;
          if(wh.is24h) hTxt='<div style="font-size:11px;margin-top:3px;color:#22c55e">🕐 {'Тәулік бойы' if kz else 'Круглосуточно'}</div>';
        }} catch(e){{}}
      }}
      
      var price = s.gasPrice;
      var pTxt = price ? '<div style="font-size:12px;margin-top:4px;font-weight:700;color:#22c55e">💰 '+price+' ₸/л</div>' : '';
      
      var svcs = s.services || [];
      var sTxt = svcs.length ? '<div style="font-size:10px;margin-top:4px;color:#64748b">'+svcs.map(function(v){{return svcNames[v]||''}}).filter(Boolean).join(' · ')+'</div>' : '';
      
      var photo = (s.photos && s.photos.length) ? '<img src="'+API+s.photos[0]+'" style="width:100%;height:100px;object-fit:cover;border-radius:8px;margin-bottom:8px" onerror="this.style.display=\\'none\\'"/>' : '';
      
      var updTxt = '';
      if(s.lastUpdated){{
        var dm = Math.floor((new Date()-new Date(s.lastUpdated))/60000);
        if(dm<5) updTxt='{'Қазір' if kz else 'Сейчас'}';
        else if(dm<60) updTxt=dm+' {'мин' if kz else 'мин'}';
        else if(dm<1440) updTxt=Math.floor(dm/60)+' {'сағ' if kz else 'ч'}';
        else updTxt=Math.floor(dm/1440)+' {'күн' if kz else 'дн'}';
      }}
      
      var premBadge = s.isPremium ? '<span style="background:linear-gradient(135deg,#f59e0b,#d97706);color:white;font-size:9px;font-weight:700;padding:1px 6px;border-radius:10px;margin-left:6px">⭐ PRO</span>' : '';
      
      var popup = '<div style="min-width:180px;font-family:-apple-system,sans-serif">'
        +photo
        +'<div style="font-weight:800;font-size:14px;margin-bottom:6px">'+s.name+premBadge+'</div>'
        +'<div style="display:inline-block;padding:3px 10px;border-radius:8px;font-size:12px;font-weight:700;background:'+c+'18;color:'+c+';border:1px solid '+c+'30">'+statusIco[s.status]+' '+statusTxt[s.status]+'</div>'
        +pTxt+qTxt+hTxt+sTxt
        +(dist?'<div style="font-size:11px;margin-top:4px;color:#64748b">📏 '+dist+'</div>':'')
        +(updTxt?'<div style="font-size:10px;margin-top:4px;color:#94a3b8">🕐 '+updTxt+'</div>':'')
        +'</div>';
      
      L.marker([s.lat,s.lon],{{icon:icon}}).addTo(map).bindPopup(popup,{{maxWidth:260}});
    }});
    if(stations.length > 0) {{
      var group = L.featureGroup(stations.map(function(s){{return L.marker([s.lat,s.lon])}}));
      map.fitBounds(group.getBounds().pad(0.1));
    }}
    setTimeout(function(){{map.invalidateSize();}},500);
  }}).catch(function(e){{console.error(e);}});
}} catch(e) {{
  document.body.innerHTML='<div style="padding:40px;text-align:center"><h2>Ошибка</h2><p>'+e.message+'</p></div>';
}}

function calcDist(lat1,lon1,lat2,lon2){{
  var R=6371,dLat=(lat2-lat1)*Math.PI/180,dLon=(lon2-lon1)*Math.PI/180;
  var a=Math.sin(dLat/2)*Math.sin(dLat/2)+Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)*Math.sin(dLon/2);
  return R*2*Math.atan2(Math.sqrt(a),Math.sqrt(1-a));
}}

function locateMe(){{
  if(!navigator.geolocation) return;
  navigator.geolocation.getCurrentPosition(function(p){{
    userLat=p.coords.latitude; userLon=p.coords.longitude;
    if(userMarker) map.removeLayer(userMarker);
    var icon=L.divIcon({{html:'<div style="width:18px;height:18px;border-radius:50%;background:#3b82f6;border:3px solid white;box-shadow:0 2px 10px rgba(59,130,246,0.6)"></div>',iconSize:[18,18],iconAnchor:[9,9],className:''}});
    userMarker=L.marker([userLat,userLon],{{icon:icon}}).addTo(map);
    map.setView([userLat,userLon],14);
  }});
}}

// Пробуем геолокацию сразу
locateMe();
</script></body></html>"""
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html)


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
    return {"status": "pending", "message": "Заявка отправлена"}

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

@app.post("/stations/{station_id}/update")
async def update_station_status(station_id: int, data: StatusUpdate, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    if auth.startswith("Bearer "):
        token = auth[7:]
        user = get_current_user(token, db)
        if user.station_id != station_id and user.role != "admin":
            raise HTTPException(status_code=403, detail="Нет доступа")
    elif auth.startswith("Trusted "):
        tg_id = auth[8:]
        trusted = db.query(TrustedUser).filter(
            TrustedUser.station_id == station_id,
            TrustedUser.telegram_id == tg_id
        ).first()
        if not trusted:
            raise HTTPException(status_code=403, detail="Нет доступа")
    else:
        raise HTTPException(status_code=401, detail="Авторизация не передана")

    old_status = get_station_status(station)
    station.status = data.status
    station.last_updated = datetime.utcnow()
    station.complaints_count = 0
    station.last_complaint_reset = datetime.utcnow()
    db.commit()

    if data.status == "green" and old_status != "green":
        subs = db.query(Subscription).filter(Subscription.station_id == station_id).all()
        for sub in subs:
            asyncio.create_task(send_tg(
                sub.telegram_id,
                f"🟢 *Газ появился!*\n📍 {station.name}\n\nСпешите!"
            ))

    return {"status": "ok", "new_status": data.status, "complaints_reset": True}

@app.put("/stations/{station_id}/status")
async def admin_change_status(station_id: int, data: StatusUpdate, db: Session = Depends(get_db)):
    """Смена статуса из админки (без авторизации — защита паролем в frontend)"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    old_status = get_station_status(station)
    station.status = data.status
    station.last_updated = datetime.utcnow()
    db.commit()
    # Уведомляем подписчиков
    if data.status == "green" and old_status != "green":
        subs = db.query(Subscription).filter(Subscription.station_id == station_id).all()
        for sub in subs:
            asyncio.create_task(send_tg(
                sub.telegram_id,
                f"🟢 *Газ появился!*\n📍 {station.name}\n\nСпешите!"
            ))
    return {"status": "ok", "new_status": data.status}

@app.post("/stations/{station_id}/hours")
async def save_working_hours(
    station_id: int,
    data: WorkingHoursRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """ИСПРАВЛЕНО: убрали Depends(get_current_user)"""
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    current_user = get_current_user(token, db)
    
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    if station.owner_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Нет доступа")

    station.working_hours = dict(data.working_hours)
    flag_modified(station, "working_hours")
    db.commit()
    db.refresh(station)
    return {"status": "ok", "working_hours": station.working_hours}
@app.post("/stations/{station_id}/price")
async def update_gas_price(
    station_id: int,
    data: GasPriceUpdate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Обновление цены газа на станции
    Доступно только владельцу станции
    """
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    
    # ВАЖНО: Только владелец может менять цену (НЕ доверенные пользователи!)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="Только владелец может изменять цену газа"
        )
    
    # Валидация цены
    if data.gas_price < 0:
        raise HTTPException(
            status_code=400, 
            detail="Цена не может быть отрицательной"
        )
    
    if data.gas_price > 10000:
        raise HTTPException(
            status_code=400, 
            detail="Цена слишком высокая (максимум 10000 ₸)"
        )
    
    # Обновляем цену
    station.gas_price = data.gas_price
    db.commit()
    db.refresh(station)
    
    return {
        "success": True,
        "station_id": station_id,
        "gas_price": data.gas_price,
        "message": "Цена газа обновлена"
    }

@app.post("/stations/{station_id}/services")
async def update_services(station_id: int, data: ServicesUpdate, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    station.services = list(data.services)
    flag_modified(station, "services")
    db.commit()
    db.refresh(station)
    print(f"🛎️ Services updated for {station.name}: {data.services}")
    return {"status": "ok", "services": station.services}

@app.post("/stations/{station_id}/queue")
async def update_queue(station_id: int, data: QueueUpdate, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    station.queue_level = data.queue_level
    db.commit()
    return {"status": "ok", "queue_level": data.queue_level}

@app.post("/stations/{station_id}/reminder")
async def update_reminder(station_id: int, data: ReminderUpdate, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    station.reminder_min = data.reminder_min
    db.commit()
    return {"status": "ok", "reminder_min": data.reminder_min}

# ═══════ ФОТО СТАНЦИИ ═══════
@app.post("/stations/{station_id}/photos")
async def upload_photo(station_id: int, file: UploadFile = File(...), request: Request = None, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "") if request else ""
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{station_id}_{uuid.uuid4().hex[:8]}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        content = await file.read()
        f.write(content)
    
    photo_url = f"/uploads/photos/{filename}"
    photos = list(station.photos or [])
    photos.append(photo_url)
    station.photos = photos
    flag_modified(station, "photos")
    db.commit()
    db.refresh(station)
    print(f"📷 Photo uploaded: {photo_url}, total: {len(station.photos)}")
    return {"status": "ok", "photos": station.photos}

@app.delete("/stations/{station_id}/photos")
async def delete_photo(station_id: int, url: str, request: Request = None, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "") if request else ""
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    if station.owner_id != user.id and user.role != "admin":
        raise HTTPException(status_code=403)
    
    photos = [p for p in (station.photos or []) if p != url]
    station.photos = photos
    flag_modified(station, "photos")
    filepath = url.lstrip('/')
    if os.path.exists(filepath):
        os.remove(filepath)
    db.commit()
    db.refresh(station)
    return {"status": "ok", "photos": station.photos}

# ═══════ ДОВЕРЕННЫЕ ПОЛЬЗОВАТЕЛИ ═══════
@app.get("/stations/{station_id}/trusted")
async def get_trusted(station_id: int, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station or (station.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=403)
    trusted = db.query(TrustedUser).filter(TrustedUser.station_id == station_id).all()
    return [{"id": t.id, "telegram_id": t.telegram_id, "name": t.name} for t in trusted]

@app.post("/stations/{station_id}/trusted")
async def add_trusted(station_id: int, data: TrustedUserAdd, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station or (station.owner_id != user.id and user.role != "admin"):
        raise HTTPException(status_code=403)
    count = db.query(TrustedUser).filter(TrustedUser.station_id == station_id).count()
    if count >= 3:
        raise HTTPException(status_code=400, detail="Максимум 3 доверенных")
    pw_hash = hash_password(data.password) if data.password else None
    tu = TrustedUser(station_id=station_id, telegram_id=data.telegram_id, name=data.name, password_hash=pw_hash, added_by=user.id)
    db.add(tu)
    db.commit()
    return {"status": "ok"}

@app.delete("/stations/{station_id}/trusted/{trusted_id}")
async def remove_trusted(station_id: int, trusted_id: int, request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    user = get_current_user(token, db)
    tu = db.query(TrustedUser).filter(TrustedUser.id == trusted_id, TrustedUser.station_id == station_id).first()
    if not tu:
        raise HTTPException(status_code=404)
    db.delete(tu)
    db.commit()
    return {"status": "ok"}

@app.post("/auth/trusted-login")
async def trusted_login(data: dict, db: Session = Depends(get_db)):
    """Вход доверенного лица по @username + пароль"""
    username = (data.get("username") or "").strip().lstrip("@")
    password = data.get("password") or ""
    if not username or not password:
        raise HTTPException(status_code=400, detail="Введите @username и пароль")
    # Ищем доверенного по telegram_id (username)
    tu = db.query(TrustedUser).filter(
        TrustedUser.telegram_id.in_([username, "@" + username])
    ).first()
    if not tu or not tu.password_hash:
        raise HTTPException(status_code=401, detail="Пользователь не найден")
    if not verify_password(password, tu.password_hash):
        raise HTTPException(status_code=401, detail="Неверный пароль")
    # Получаем станцию
    station = db.query(Station).filter(Station.id == tu.station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    return {
        "trusted_id": tu.id,
        "name": tu.name,
        "station_id": station.id,
        "station_name": station.name,
        "station_status": get_station_status(station),
        "station": station_to_dict(station)
    }

@app.post("/trusted/{trusted_id}/update-status")
async def trusted_update_status(trusted_id: int, data: StatusUpdate, db: Session = Depends(get_db)):
    """Доверенное лицо обновляет статус газа"""
    tu = db.query(TrustedUser).filter(TrustedUser.id == trusted_id).first()
    if not tu:
        raise HTTPException(status_code=404)
    station = db.query(Station).filter(Station.id == tu.station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    old_status = station.status
    station.status = data.status
    station.last_updated = datetime.utcnow()
    db.commit()
    # Уведомляем подписчиков если газ появился
    if data.status == "green" and old_status != "green":
        subs = db.query(Subscription).filter(Subscription.station_id == tu.station_id).all()
        for sub in subs:
            asyncio.create_task(send_tg(sub.telegram_id, f"🟢 *Газ появился!*\n📍 {station.name}\n\nСпешите!"))
    return {"status": "ok", "new_status": data.status}

@app.post("/trusted/{trusted_id}/update-queue")
async def trusted_update_queue(trusted_id: int, data: QueueUpdate, db: Session = Depends(get_db)):
    """Доверенное лицо обновляет очередь"""
    tu = db.query(TrustedUser).filter(TrustedUser.id == trusted_id).first()
    if not tu:
        raise HTTPException(status_code=404)
    station = db.query(Station).filter(Station.id == tu.station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    station.queue_level = data.queue_level
    db.commit()
    return {"status": "ok"}

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

@app.post("/stations/{station_id}/complain")
async def submit_complaint(station_id: int, data: ComplaintCreate, db: Session = Depends(get_db)):
    """Подать жалобу на станцию (для водителей)"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    
    # Проверяем дубликат (один юзер = одна жалоба в сутки на одну станцию)
    one_day_ago = datetime.utcnow() - timedelta(days=1)
    existing = db.query(Complaint).filter(
        Complaint.station_id == station_id,
        Complaint.user_telegram_id == data.user_telegram_id,
        Complaint.created_at >= one_day_ago
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Вы уже жаловались на эту станцию сегодня")
    
    # Сохраняем жалобу
    complaint = Complaint(
        station_id=station_id,
        user_telegram_id=data.user_telegram_id,
        reason=data.reason,
        comment=data.comment,
        photo_url=data.photo_url
    )
    db.add(complaint)
    
    # Считаем активные жалобы (за последние 7 дней от РАЗНЫХ пользователей)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active_complaints_count = db.query(Complaint.user_telegram_id).filter(
        Complaint.station_id == station_id,
        Complaint.created_at >= seven_days_ago
    ).distinct().count()
    
    # Обновляем счетчик
    station.complaints_count = active_complaints_count
    
    # Проверяем порог (5 жалоб)
    status_changed = False
    if active_complaints_count >= 5:
        station.status = "purple"
        station.complaints_count = 0
        station.last_complaint_reset = datetime.utcnow()
        status_changed = True
        
        # Отправляем уведомление владельцу
        owner = db.query(User).filter(User.station_id == station_id).first()
        if owner and owner.telegram_id:
            message = (
                f"⚠️ *ВНИМАНИЕ!*\n\n"
                f"Ваша станция *{station.name}* получила *{active_complaints_count} жалоб* "
                f"от водителей на недостоверную информацию.\n\n"
                f"Статус станции автоматически изменен на 🟣 *Неизвестно*.\n\n"
                f"🔄 Обновите статус газа в кабинете владельца, "
                f"чтобы восстановить репутацию станции."
            )
            asyncio.create_task(send_telegram_notification(owner.telegram_id, message))
    
    db.commit()
    
    return {
        "success": True,
        "message": "Жалоба принята. Спасибо за помощь!" if not status_changed 
                   else "Жалоба принята. Статус станции изменен на 'Неизвестно'",
        "complaints_count": active_complaints_count if not status_changed else 0,
        "threshold": 5,
        "status_changed": status_changed
    }

@app.get("/stations/{station_id}/complaints/count")
async def get_complaints_count(station_id: int, db: Session = Depends(get_db)):
    """Получить количество активных жалоб"""
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    count = db.query(Complaint.user_telegram_id).filter(
        Complaint.station_id == station_id,
        Complaint.created_at >= seven_days_ago
    ).distinct().count()
    
    return {
        "station_id": station_id,
        "complaints_count": count,
        "threshold": 5
    }

@app.get("/stations/{station_id}/complaints/details")
async def get_station_complaints(station_id: int, db: Session = Depends(get_db)):
    """Получить детали жалоб (для владельца)"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    complaints = db.query(Complaint).filter(
        Complaint.station_id == station_id,
        Complaint.created_at >= seven_days_ago
    ).order_by(Complaint.created_at.desc()).all()
    
    # Группируем по причинам
    by_reason = {}
    for c in complaints:
        if c.reason not in by_reason:
            by_reason[c.reason] = 0
        by_reason[c.reason] += 1
    
    return {
        "station_id": station_id,
        "total_complaints": len(complaints),
        "complaints_by_reason": by_reason,
        "complaints": [
            {
                "id": c.id,
                "reason": c.reason,
                "comment": c.comment,
                "created_at": c.created_at.isoformat()
            } for c in complaints
        ]
    }

@app.post("/stations/{station_id}/complaint")

async def file_complaint(station_id: int, data: ComplaintRequest, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")

    threshold = int(get_setting(db, "complaint_threshold", "5"))
    last_upd = station.last_updated.isoformat() if station.last_updated else ""

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
        status_snapshot=station.status,
    )
    db.add(complaint)
    db.commit()

    count = db.query(Complaint).filter(
        Complaint.station_id == station_id,
        Complaint.last_updated_snapshot == last_upd
    ).count()

    status_changed = False
    if count >= threshold and station.status != "purple":
        station.status = "purple"
        db.commit()
        status_changed = True

    return {
        "status": "ok",
        "complaint_count": count,
        "threshold": threshold,
        "status_changed": status_changed,
        "new_status": station.status
    }

@app.post("/feedback")
async def submit_feedback(data: FeedbackRequest, db: Session = Depends(get_db)):
    if not data.text.strip():
        raise HTTPException(status_code=400, detail="Пустое сообщение")
    fb = Feedback(
        category=data.category,
        text=data.text.strip()[:1000],
        station_id=data.station_id,
        telegram_id=data.telegram_id,
        lang=data.lang or "ru",
    )
    db.add(fb)
    db.commit()
    return {"status": "ok"}

@app.get("/admin/feedback")
async def admin_get_feedback(request: Request, db: Session = Depends(get_db)):
    auth = request.headers.get("Authorization", "")
    token = get_token_from_header(auth)
    admin = get_current_user(token, db)
    if admin.role != "admin":
        raise HTTPException(status_code=403)
    items = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(100).all()
    result = []
    for f in items:
        station_name = None
        if f.station_id:
            st = db.query(Station).filter(Station.id == f.station_id).first()
            if st: station_name = st.name
        result.append({
            "id": f.id,
            "category": f.category,
            "text": f.text,
            "station_id": f.station_id,
            "station_name": station_name,
            "telegram_id": f.telegram_id,
            "lang": f.lang,
            "created_at": f.created_at.isoformat(),
        })
    return result

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
async def admin_approve(user_id: int, db: Session = Depends(get_db)):
    """Одобрить владельца (без токена — admin.html защищена паролем)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    user.is_approved = True
    if user.station_id:
        station = db.query(Station).filter(Station.id == user.station_id).first()
        if station:
            station.owner_id = user.id
            print(f"✅ Станция '{station.name}' привязана к {user.name}")
    db.commit()
    print(f"✅ Пользователь {user.name} одобрен")
    return {"status": "ok", "message": f"Пользователь {user.name} одобрен"}

@app.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, db: Session = Depends(get_db)):
    """Удалить пользователя (без токена — admin.html защищена паролем)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404)
    db.delete(user)
    db.commit()
    return {"status": "ok"}

@app.post("/admin/stations")
async def admin_create_station(data: StationCreate, db: Session = Depends(get_db)):
    """Создать станцию (упрощённая проверка для админки)"""
    # Упрощённая админка - без токена, защита паролем в frontend
    station = Station(
        name=data.name, 
        lat=data.lat, 
        lon=data.lon, 
        description=data.description,
        phone=data.phone,
        status="purple"
    )
    db.add(station)
    db.commit()
    db.refresh(station)
    return station_to_dict(station)

@app.post("/admin/stations/{station_id}/premium")
async def admin_toggle_premium(station_id: int, data: dict, db: Session = Depends(get_db)):
    """Дать/отозвать Premium статус станции"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    station.is_premium = bool(data.get("is_premium", False))
    if station.is_premium and not station.premium_until:
        station.premium_until = datetime.utcnow() + timedelta(days=30)
    elif not station.is_premium:
        station.premium_until = None
    db.commit()
    print(f"⭐ Premium {'ON' if station.is_premium else 'OFF'} для {station.name}")
    return {"status": "ok", "is_premium": station.is_premium}

@app.delete("/admin/stations/{station_id}")
async def admin_delete_station(station_id: int, db: Session = Depends(get_db)):
    """Удалить станцию (упрощённая проверка)"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    db.query(User).filter(User.station_id == station_id).update({"station_id": None})
    db.query(TrustedUser).filter(TrustedUser.station_id == station_id).delete()
    db.query(Subscription).filter(Subscription.station_id == station_id).delete()
    db.query(Complaint).filter(Complaint.station_id == station_id).delete()
    db.delete(station)
    db.commit()
    return {"status": "ok"}

@app.put("/admin/stations/{station_id}")
async def admin_update_station(station_id: int, data: StationCreate, db: Session = Depends(get_db)):
    """Редактировать станцию"""
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Станция не найдена")
    
    station.name = data.name
    station.lat = data.lat
    station.lon = data.lon
    station.description = data.description
    if hasattr(data, 'phone'):
        station.phone = data.phone
    
    db.commit()
    db.refresh(station)
    return station_to_dict(station)

@app.post("/admin/users/{user_id}/reject")
async def admin_reject_user(user_id: int, db: Session = Depends(get_db)):
    """Отклонить заявку пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Можно либо удалить пользователя, либо пометить как отклоненный
    # Вариант 1: Удаление
    db.delete(user)
    db.commit()
    return {"status": "ok", "message": "Пользователь удален"}

@app.get("/admin/registrations")
async def admin_get_registrations(db: Session = Depends(get_db)):
    """Получить список регистраций владельцев (БЕЗ токена для админки)"""
    users = db.query(User).filter(User.role == "owner").all()
    
    result = []
    for user in users:
        station_name = None
        if user.station_id:
            station = db.query(Station).filter(Station.id == user.station_id).first()
            if station:
                station_name = station.name
        
        result.append({
            "id": user.id,
            "name": user.name,
            "phone": user.phone,
            "telegram_id": user.telegram_id,
            "station_id": user.station_id,
            "station_name": station_name,
            "is_approved": user.is_approved,
            "created_at": user.created_at.isoformat() if user.created_at else None
        })
    
    return result

@app.get("/admin/analytics")
async def admin_get_analytics(db: Session = Depends(get_db)):
    """Получить статистику посещений и активности"""
    # Общее количество пользователей
    total_users = db.query(User).count()
    
    # Владельцы и водители (по роли)
    owners = db.query(User).filter(User.role == "owner").count()
    drivers = total_users - owners  # Все остальные - водители
    
    # Можно добавить таблицу для логирования визитов
    # Пока возвращаем базовую статистику
    
    return {
        "total_users": total_users,
        "owners": owners,
        "drivers": drivers,
        "total_stations": db.query(Station).count(),
        "premium_stations": db.query(Station).filter(Station.is_premium == True).count()
    }

@app.get("/admin/complaints")
async def admin_get_complaints(db: Session = Depends(get_db)):
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    complaints = db.query(Complaint).filter(
        Complaint.created_at >= thirty_days_ago
    ).order_by(Complaint.created_at.desc()).limit(100).all()
    
    result = []
    for c in complaints:
        station = db.query(Station).filter(Station.id == c.station_id).first()
        result.append({
            "id": c.id,
            "station_id": c.station_id,
            "station_name": station.name if station else "Неизвестно",
            "user_telegram_id": c.user_telegram_id,
            "reason": c.reason,
            "comment": c.comment,
            "created_at": c.created_at.isoformat()
        })
    return result

@app.get("/admin/complaints/stats")
async def admin_get_complaints_stats(db: Session = Depends(get_db)):
    
    # Всего жалоб
    total = db.query(Complaint).count()
    
    # Активных за 7 дней
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    active = db.query(Complaint).filter(Complaint.created_at >= seven_days_ago).count()
    
    # По причинам
    complaints = db.query(Complaint).all()
    by_reason = {}
    for c in complaints:
        if c.reason not in by_reason:
            by_reason[c.reason] = 0
        by_reason[c.reason] += 1
    
    # Топ станций с жалобами
    from sqlalchemy import func
    top_stations = db.query(
        Station.id,
        Station.name,
        func.count(Complaint.id).label('count')
    ).join(Complaint, Station.id == Complaint.station_id).filter(
        Complaint.created_at >= seven_days_ago
    ).group_by(Station.id).order_by(func.count(Complaint.id).desc()).limit(10).all()
    
    return {
        "total_complaints": total,
        "active_complaints": active,
        "complaints_by_reason": by_reason,
        "top_complained_stations": [
            {"id": s.id, "name": s.name, "complaints_count": s.count}
            for s in top_stations
        ]
    }

@app.post("/admin/complaints/{station_id}/reset")
async def admin_reset_complaints(station_id: int, db: Session = Depends(get_db)):
    station = db.query(Station).filter(Station.id == station_id).first()
    if not station:
        raise HTTPException(status_code=404)
    station.last_updated = datetime.utcnow()
    db.commit()
    return {"status": "ok"}

@app.get("/admin/settings")
async def admin_get_settings(db: Session = Depends(get_db)):
    return {
        "complaint_threshold": get_setting(db, "complaint_threshold", "5"),
        "admin_tg_id":  get_setting(db, "admin_tg_id", ""),
        "admin_tg_ids": get_setting(db, "admin_tg_ids", ""),
    }

@app.post("/admin/settings")
async def admin_update_settings(data: dict, db: Session = Depends(get_db)):
    if "complaint_threshold" in data:
        val = int(data["complaint_threshold"])
        if not 1 <= val <= 100:
            raise HTTPException(status_code=400, detail="Порог должен быть от 1 до 100")
        set_setting(db, "complaint_threshold", str(val))
    if "admin_tg_id" in data:
        set_setting(db, "admin_tg_id", str(data["admin_tg_id"]))
    if "admin_tg_ids" in data:
        set_setting(db, "admin_tg_ids", str(data["admin_tg_ids"]))
    return {"status": "ok"}

# Статические файлы
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
except Exception:
    pass

# ══════════════════════════════════════════
# МИГРАЦИИ (добавление новых колонок)
# ══════════════════════════════════════════
def migrate():
    import sqlite3
    db_path = DATABASE_URL.replace("sqlite:///./", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # Добавляем password_hash в trusted_users если нет
    try:
        cursor.execute("ALTER TABLE trusted_users ADD COLUMN password_hash TEXT")
        print("✅ Migration: added password_hash to trusted_users")
    except:
        pass
    try:
        cursor.execute("ALTER TABLE stations ADD COLUMN phone TEXT")
        print("✅ Migration: added phone to stations")
    except:
        pass
    conn.commit()
    conn.close()

migrate()

# ══════════════════════════════════════════
# SEED
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)