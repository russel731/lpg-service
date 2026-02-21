import os
import requests

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")


def get_nearby_stations(lat: float, lon: float, radius_km: int = 10):
    try:
        response = requests.get(
            f"{BACKEND_URL}/stations/nearby",
            params={
                "lat": lat,
                "lon": lon,
                "radius_km": radius_km
            },
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("API ERROR:", e)
        return []
