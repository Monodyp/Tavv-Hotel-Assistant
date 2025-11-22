import sqlite3
import os

DB_PATH = os.path.join("data", "hotel.db")
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---------------------------
# 0. Resident Check-in
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS residents (
    resident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    room_number TEXT NOT NULL,
    device_token TEXT UNIQUE NOT NULL,
    checkin_time TEXT,
    checkout_time TEXT,
    token_voided INTEGER DEFAULT 0,
    FOREIGN KEY(room_number) REFERENCES rooms(room_number)
)
""")

# ---------------------------
# 1. Buildings
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS buildings (
    building_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    wifi_ssid TEXT,
    wifi_password TEXT,
    restaurant_name TEXT
)
""")

# ---------------------------
# 2. Rooms
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS rooms (
    room_number TEXT PRIMARY KEY,
    building_id INTEGER,
    floor INTEGER,
    room_type TEXT,
    tv_brand TEXT,
    fan_type TEXT,
    thermostat_model TEXT,
    FOREIGN KEY(building_id) REFERENCES buildings(building_id)
)
""")

# ---------------------------
# 3. Amenities
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS amenities (
    amenity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER,
    name TEXT,
    description TEXT,
    floor INTEGER,
    FOREIGN KEY(building_id) REFERENCES buildings(building_id)
)
""")

# ---------------------------
# 4. Pools
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS pools (
    pool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    features TEXT
)
""")

# ---------------------------
# 5. Water Sports Activities
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS water_sports (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT
)
""")

# ---------------------------
# 6. Restaurant Menu
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS restaurant_menu (
    menu_id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT,
    meal TEXT,
    item_name TEXT,
    restaurant_name TEXT
)
""")

conn.commit()
conn.close()

print("Database schema initialized successfully!")
