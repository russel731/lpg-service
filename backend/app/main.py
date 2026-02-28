from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import os

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👉 путь к фронтенду
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), "..", "frontend", "out")


# 🔥 Главная страница для Telegram
@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_PATH, "index.html"))


# 🔥 станции
stations_data = [
    {
        "id": 1,
        "name": "Газ Актау 1",
        "lat": 43.65,
        "lng": 51.16,
        "status": "available",
    },
    {
        "id": 2,
        "name": "Газ Актау 2",
        "lat": 43.66,
        "lng": 51.14,
        "status": "low",
    },
    {
        "id": 3,
        "name": "Газ Актау 3",
        "lat": 43.67,
        "lng": 51.15,
        "status": "empty",
    },
]


@app.get("/stations")
def get_stations():
    return stations_data