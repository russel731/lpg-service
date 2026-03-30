import sqlite3

conn = sqlite3.connect('lpg.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE stations ADD COLUMN complaints_count INTEGER DEFAULT 0")
    print(" complaints_count добавлен")
except Exception as e:
    print(f" complaints_count: {e}")

try:
    cursor.execute("ALTER TABLE stations ADD COLUMN last_complaint_reset TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    print(" last_complaint_reset добавлен")
except Exception as e:
    print(f" last_complaint_reset: {e}")

try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN user_telegram_id TEXT")
    print(" user_telegram_id добавлен")
except Exception as e:
    print(f" user_telegram_id: {e}")

try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN reason TEXT")
    print(" reason добавлен")
except Exception as e:
    print(f" reason: {e}")

try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN comment TEXT")
    print(" comment добавлен")
except Exception as e:
    print(f" comment: {e}")

try:
    cursor.execute("ALTER TABLE complaints ADD COLUMN photo_url TEXT")
    print(" photo_url добавлен")
except Exception as e:
    print(f" photo_url: {e}")

conn.commit()
conn.close()
print("\n МИГРАЦИЯ ЗАВЕРШЕНА!")
