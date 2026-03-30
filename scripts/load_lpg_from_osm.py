import requests
import pandas as pd


# 📍 Алматы координаты (можно менять)
LAT_MIN = 43.0
LON_MIN = 76.5
LAT_MAX = 43.5
LON_MAX = 77.2


OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def fetch_lpg_stations():
    query = f"""
    [out:json];
    (
      node["amenity"="fuel"]( {LAT_MIN},{LON_MIN},{LAT_MAX},{LON_MAX} );
    );
    out;
    """

    print("🔄 Запрос к OpenStreetMap...")

    response = requests.post(OVERPASS_URL, data=query)
    response.raise_for_status()

    data = response.json()

    stations = []

    for el in data["elements"]:
        tags = el.get("tags", {})

        # 🔥 фильтр LPG
        if tags.get("fuel:lpg") != "yes":
            continue

        stations.append({
            "name": tags.get("name", "Unknown"),
            "lat": el["lat"],
            "lon": el["lon"],
            "phone": tags.get("phone", ""),
            "brand": tags.get("brand", ""),
            "address": tags.get("addr:full", ""),
            "city": tags.get("addr:city", ""),
        })

    print(f"✅ Найдено LPG станций: {len(stations)}")

    return stations


def save_excel(stations):
    df = pd.DataFrame(stations)
    df.to_excel("lpg_stations.xlsx", index=False)
    print("📊 Excel файл создан: lpg_stations.xlsx")


if __name__ == "__main__":
    stations = fetch_lpg_stations()
    save_excel(stations)