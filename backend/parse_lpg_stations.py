"""
Скрипт для автоматического добавления всех АГЗС Казахстана в базу данных
Использует OpenStreetMap (бесплатно, без регистрации)
"""

import requests
import sqlite3
import time

# ════════════════════════════════════════
# НАСТРОЙКИ
# ════════════════════════════════════════

DB_PATH = "lpg.db"  # Путь к базе данных

# Города Казахстана для поиска
CITIES = [
    {"name": "Актау", "lat": 43.6508, "lon": 51.1601},
    {"name": "Алматы", "lat": 43.2220, "lon": 76.8512},
    {"name": "Астана", "lat": 51.1694, "lon": 71.4491},
    {"name": "Шымкент", "lat": 42.3000, "lon": 69.6000},
    {"name": "Караганда", "lat": 49.8047, "lon": 73.1094},
    {"name": "Атырау", "lat": 47.1164, "lon": 51.8830},
    {"name": "Павлодар", "lat": 52.2873, "lon": 76.9674},
    {"name": "Усть-Каменогорск", "lat": 49.9488, "lon": 82.6278},
    {"name": "Семей", "lat": 50.4111, "lon": 80.2275},
    {"name": "Тараз", "lat": 42.9000, "lon": 71.3667},
    {"name": "Костанай", "lat": 53.2141, "lon": 63.6246},
    {"name": "Кызылорда", "lat": 44.8479, "lon": 65.5093},
    {"name": "Уральск", "lat": 51.2333, "lon": 51.3667},
    {"name": "Петропавловск", "lat": 54.8667, "lon": 69.1500},
    {"name": "Актобе", "lat": 50.2839, "lon": 57.1670},
]

RADIUS = 50000  # Радиус поиска в метрах (50 км)

# ════════════════════════════════════════
# ФУНКЦИЯ ПАРСИНГА
# ════════════════════════════════════════

def fetch_lpg_stations_for_city(city_name, lat, lon, radius):
    """
    Получить все АГЗС в указанном городе через OpenStreetMap
    """
    print(f"\n🔍 Ищем АГЗС в городе {city_name}...")
    
    # Overpass API запрос
    query = f"""
    [out:json][timeout:60];
    (
      node["amenity"="fuel"]["fuel:lpg"="yes"](around:{radius},{lat},{lon});
      way["amenity"="fuel"]["fuel:lpg"="yes"](around:{radius},{lat},{lon});
      node["amenity"="fuel"]["name"~"АГЗС|ГАЗ|LPG",i](around:{radius},{lat},{lon});
      way["amenity"="fuel"]["name"~"АГЗС|ГАЗ|LPG",i](around:{radius},{lat},{lon});
    );
    out center;
    """
    
    url = "https://overpass-api.de/api/interpreter"
    
    # Пробуем 3 раза с увеличивающейся задержкой
    for attempt in range(3):
        try:
            print(f"  Попытка {attempt + 1}/3...")
            response = requests.post(url, data={'data': query}, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            stations = []
            for element in data.get('elements', []):
                tags = element.get('tags', {})
                name = tags.get('name', f'АГЗС {city_name}')
                
                # Получаем координаты
                if 'lat' in element and 'lon' in element:
                    station_lat = element['lat']
                    station_lon = element['lon']
                elif 'center' in element:
                    station_lat = element['center']['lat']
                    station_lon = element['center']['lon']
                else:
                    continue
                
                # Получаем дополнительную информацию
                address = tags.get('addr:street', '')
                if tags.get('addr:housenumber'):
                    address += f", {tags.get('addr:housenumber')}"
                
                phone = tags.get('phone', tags.get('contact:phone', ''))
                
                stations.append({
                    'name': name,
                    'lat': station_lat,
                    'lon': station_lon,
                    'city': city_name,
                    'address': address or f"{city_name}, Казахстан",
                    'phone': phone
                })
            
            print(f"✅ Найдено {len(stations)} станций в городе {city_name}")
            return stations
            
        except requests.exceptions.Timeout:
            print(f"  ⏱️ Таймаут. Ждём {(attempt + 1) * 10} секунд...")
            time.sleep((attempt + 1) * 10)
            continue
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                wait_time = (attempt + 1) * 20
                print(f"  ⏸️ Слишком много запросов. Ждём {wait_time} секунд...")
                time.sleep(wait_time)
                continue
            else:
                print(f"❌ HTTP ошибка для города {city_name}: {e}")
                return []
                
        except Exception as e:
            print(f"❌ Ошибка для города {city_name}: {e}")
            return []
    
    print(f"❌ Не удалось получить данные для города {city_name} после 3 попыток")
    return []

# ════════════════════════════════════════
# ФУНКЦИЯ СОХРАНЕНИЯ В БД
# ════════════════════════════════════════

def save_stations_to_db(stations):
    """
    Сохранить станции в базу данных
    """
    if not stations:
        print("⚠️ Нет станций для сохранения")
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    added = 0
    skipped = 0
    
    for station in stations:
        try:
            # Проверяем дубликаты (по координатам)
            cursor.execute("""
                SELECT id FROM stations 
                WHERE ABS(lat - ?) < 0.001 AND ABS(lon - ?) < 0.001
            """, (station['lat'], station['lon']))
            
            if cursor.fetchone():
                skipped += 1
                continue
            
            # Добавляем станцию
            cursor.execute("""
                INSERT INTO stations 
                (name, lat, lon, status, description, last_updated) 
                VALUES (?, ?, ?, 'purple', ?, CURRENT_TIMESTAMP)
            """, (
                station['name'],
                station['lat'],
                station['lon'],
                station['address']
            ))
            
            added += 1
            print(f"  ✅ Добавлено: {station['name']}")
            
        except sqlite3.Error as e:
            print(f"  ❌ Ошибка при добавлении {station['name']}: {e}")
            continue
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Итого: добавлено {added}, пропущено дубликатов {skipped}")
    return added

# ════════════════════════════════════════
# ГЛАВНАЯ ФУНКЦИЯ
# ════════════════════════════════════════

def main():
    """
    Основная функция парсинга
    """
    print("🚀 НАЧИНАЕМ ПАРСИНГ АГЗС КАЗАХСТАНА")
    print("=" * 50)
    
    all_stations = []
    
    for city in CITIES:
        # Парсим город
        stations = fetch_lpg_stations_for_city(
            city['name'],
            city['lat'],
            city['lon'],
            RADIUS
        )
        
        all_stations.extend(stations)
        
        # Большая задержка между запросами (чтобы не перегружать API)
        print(f"  ⏸️ Ждём 15 секунд перед следующим городом...")
        time.sleep(15)
    
    print("\n" + "=" * 50)
    print(f"🎯 ВСЕГО НАЙДЕНО: {len(all_stations)} станций")
    print("=" * 50)
    
    # Сохраняем в БД
    if all_stations:
        print("\n💾 Сохраняем в базу данных...")
        total_added = save_stations_to_db(all_stations)
        
        print("\n" + "=" * 50)
        print(f"🎉 ГОТОВО! Добавлено {total_added} новых станций")
        print("=" * 50)
    else:
        print("\n⚠️ Не найдено ни одной станции")
    
    # Показываем статистику
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM stations")
    total = cursor.fetchone()[0]
    conn.close()
    
    print(f"\n📊 Всего станций в базе: {total}")

# ════════════════════════════════════════
# ЗАПУСК
# ════════════════════════════════════════

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Парсинг прерван пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
