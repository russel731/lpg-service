"""
Импорт АГЗС Актау | cd backend && python import_stations.py
"""
import sqlite3, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "lpg.db")

STATIONS = [
    # (название, lat, lon, адрес, телефон)
    ("Qazaq Oil АГЗС 29а/114", 43.6536, 51.1503, "29а мкр, 114/1", "+7 7292 000000"),
    ("Qazaq Oil АГЗС 29а/139", 43.6495, 51.1630, "29а мкр, 139", None),
    ("Qazaq Oil АГЗС 29а/128", 43.6470, 51.1530, "29а мкр, 128", None),
    ("Tulpar АГЗС 25 мкр", 43.6612, 51.1743, "25-й мкр, 9/1", None),
    ("Атбұлақ АГЗС", 43.6655, 51.1901, "ул. Ақмаржан, 49/1", None),
    ("АГЗС Промзона 2", 43.6401, 51.2012, "Промышленная зона 2, 20/1", None),
    ("АГЗС Промзона 3", 43.6380, 51.2060, "Промышленная зона 3, 90/3", None),
    ("АГЗС Промзона 4", 43.6355, 51.2095, "Промышленная зона 4, 19/9", None),
    ("АГЗС Промзона 8", 43.6310, 51.2140, "Промышленная зона 8, 73/3", None),
    ("АГЗС Промзона 9", 43.6280, 51.2180, "Промышленная зона 9, 2", None),
    ("АГЗС Промзона 9/2", 43.6265, 51.2200, "Промышленная зона 9, 6/3", None),
    ("АГЗС Промзона 9/3", 43.6250, 51.2165, "Промышленная зона 9, 45/3", None),
    ("АГЗС Промзона 9/4", 43.6245, 51.2210, "Промышленная зона 9, 45/10", None),
    ("АГЗС 16 мкр", 43.6560, 51.1460, "16-й мкр, 24/2", None),
    ("TanaGas АГЗС 19 мкр", 43.6662, 51.1735, "19-й мкр", None),
    ("АГЗС 8А мкр", 43.6700, 51.1500, "8А мкр, 8", None),
]

def import_stations():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    existing = cursor.execute("SELECT name, lat, lon FROM stations").fetchall()
    existing_set = {(round(lat, 3), round(lon, 3)) for _, lat, lon in existing}
    added = skipped = 0
    now = datetime.utcnow().isoformat()

    for name, lat, lon, desc, phone in STATIONS:
        is_dup = any(abs(elat - round(lat, 3)) < 0.003 and abs(elon - round(lon, 3)) < 0.003 for elat, elon in existing_set)
        if is_dup:
            print(f"  ⏭️  Пропуск: {name}")
            skipped += 1
            continue
        cursor.execute(
            "INSERT INTO stations (name, lat, lon, status, description, phone, last_updated, is_premium, services, photos, queue_level) VALUES (?,?,?,?,?,?,?,0,'[]','[]',0)",
            (name, lat, lon, "purple", desc, phone, now)
        )
        existing_set.add((round(lat, 3), round(lon, 3)))
        added += 1
        print(f"  ✅ {name} [{lat}, {lon}] {desc}")

    conn.commit()
    conn.close()
    print(f"\n✅ Добавлено: {added} | ⏭️ Пропущено: {skipped} | 📊 Всего: {added + len(existing)}")

if __name__ == "__main__":
    print(f"🗺️ Импорт АГЗС Актау — {len(STATIONS)} станций\n")
    import_stations()
