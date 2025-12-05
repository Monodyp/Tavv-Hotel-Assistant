import sqlite3
import os

DB_PATH = os.path.join("data", "hotel.db")
os.makedirs("data", exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# ---------------------------
# 1. Housekeeping
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS housekeeping_log (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    room_number TEXT NOT NULL,
    cleaned_time TEXT NOT NULL,
    cleaner_name TEXT NOT NULL,
    FOREIGN KEY(room_number) REFERENCES rooms(room_number)
)
""")

# ---------------------------
# 2. Hotel
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS hotel (
    hotel_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE,
    location TEXT ,
    nearby_restaurants TEXT ,
    fun_destinations TEXT
)
""")

# ---------------------------
# 3. Resident Check-in
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
# 4. Buildings
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
# 5. Rooms
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
# 6. Amenities
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
# 7. Pools
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS pools (
    pool_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    features TEXT
)
""")

# ---------------------------
# 8. Water Sports Activities
# ---------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS water_sports (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    description TEXT
)
""")

# ---------------------------
# 9. Restaurant Menu
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
