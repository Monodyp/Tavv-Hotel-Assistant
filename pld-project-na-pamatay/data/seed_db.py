import sqlite3
import os
import uuid
import datetime

DB_PATH = os.path.join("data", "hotel.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()


def seed_resident(name, room_number, device_file):
    token = str(uuid.uuid4())
    checkin_time = datetime.datetime.now().isoformat()

    # Insert or update resident
    cursor.execute("""
        INSERT INTO residents (name, room_number, device_token, checkin_time)
        VALUES (?, ?, ?, ?)
    """, (name, room_number, token, checkin_time))

    # Write token to device file
    with open(device_file, "w") as f:
        f.write(token)
    return token


def check_out_resident(token):
    checkout_time = datetime.datetime.now().isoformat()
    cursor.execute("""
        UPDATE residents
        SET checkout_time = ?, token_voided = 1
        WHERE device_token = ?
    """, (checkout_time, token))
    conn.commit()
    # remove token file if exists
    if os.path.exists("device_token.txt"):
        os.remove("device_token.txt")
    print(f"Resident with token {token} checked out. Token voided and removed from device.")

# ---------------------------
# 1. Buildings
# ---------------------------
buildings = [
    ("Main Building", "CanyonWifi", "LobXeen", "Island Cafe"),
    ("Second Building", "CoveWifi", "PatRoox", "Island Cafe")
]

cursor.executemany("""
INSERT OR IGNORE INTO buildings (name, wifi_ssid, wifi_password, restaurant_name)
VALUES (?, ?, ?, ?)
""", buildings)

# Fetch building_ids
cursor.execute("SELECT building_id FROM buildings WHERE name='Main Building'")
main_id = cursor.fetchone()[0]
cursor.execute("SELECT building_id FROM buildings WHERE name='Second Building'")
second_id = cursor.fetchone()[0]

# ---------------------------
# 2. Rooms
# ---------------------------
# Room Types per Floor
floor_room_types = {
    1: ["Superior King", "Superior Twin", "Superior King", "Superior Twin", "Superior King"],
    2: ["Bedroom Deluxe", "Bedroom Family", "Bedroom Deluxe", "Bedroom Family", "Bedroom Deluxe"],
    3: ["Bedroom Executive"]*5
}

# Main Building Rooms
main_rooms = []
room_numbers_main = [111,112,113,114,115,121,122,123,124,125,131,132,133,134,135]
for i, num in enumerate(room_numbers_main):
    floor = (i//5)+1
    room_type = floor_room_types[floor][i%5]
    main_rooms.append((str(num), main_id, floor, room_type, "Samsung", "Ceiling Fan", "Nest V3"))

# Second Building Rooms
second_rooms = []
room_numbers_second = [211,212,213,214,215,221,222,223,224,225,231,232,233,234,235]
for i, num in enumerate(room_numbers_second):
    floor = (i//5)+1
    room_type = floor_room_types[floor][i%5]
    second_rooms.append((str(num), second_id, floor, room_type, "LG", "Tower Fan", "Honeywell T6"))

cursor.executemany("""
INSERT OR IGNORE INTO rooms (room_number, building_id, floor, room_type, tv_brand, fan_type, thermostat_model)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", main_rooms + second_rooms)

# ---------------------------
# 3. Amenities
# ---------------------------
amenities = [
    (main_id, "Housekeeping", "Daily room cleaning service", 1),
    (main_id, "Communal Restroom", "Restrooms for guests on each floor", 1),
    (second_id, "Housekeeping", "Daily room cleaning service", 1),
    (second_id, "Communal Restroom", "Restrooms for guests on each floor", 1)
]

cursor.executemany("""
INSERT OR IGNORE INTO amenities (building_id, name, description, floor)
VALUES (?, ?, ?, ?)
""", amenities)

# ---------------------------
# 4. Pools
# ---------------------------
pools = [
    ("Main Pool", "Slides, Rides"),
    ("Wave Pool", "Wave feature"),
    ("Kids Pool", "Shallow, small slides"),
    ("Relax Pool", "Jacuzzi, loungers"),
    ("Sport Pool", "Lanes for swimming"),
    ("Adventure Pool", "Obstacle course, climbing features")
]

cursor.executemany("INSERT OR IGNORE INTO pools (name, features) VALUES (?, ?)", pools)

# ---------------------------
# 5. Water Sports
# ---------------------------
water_sports = [
    ("Jet Skiing", "High-speed rides along the cove"),
    ("Banana Boat", "Fun group ride"),
    ("Kayaking", "Explore the shoreline"),
    ("Snorkeling", "Discover marine life"),
    ("Parasailing", "Fly over the ocean")
]

cursor.executemany("""
INSERT OR IGNORE INTO water_sports (name, description)
VALUES (?, ?)
""", water_sports)

# ---------------------------
# 6. Restaurant Menu (Island Cafe)
# ---------------------------
menus = [
    ("Monday", "Breakfast", "Breakfast Buffet", "Island Cafe"),
    ("Thursday", "Breakfast", "Breakfast Buffet", "Island Cafe"),
    ("Sunday", "Breakfast", "Breakfast Buffet", "Island Cafe"),
    ("Tuesday", "Brunch", "Brunch Buffet", "Island Cafe"),
    ("Friday", "Brunch", "Brunch Buffet", "Island Cafe"),
    ("Monday", "Lunch", "Grilled Chicken Salad", "Island Cafe"),
    ("Monday", "Lunch", "Vegetable Stir Fry", "Island Cafe"),
    ("Tuesday", "Lunch", "Beef Burger", "Island Cafe"),
    ("Tuesday", "Lunch", "Quinoa Bowl", "Island Cafe")
]

cursor.executemany("""
INSERT OR IGNORE INTO restaurant_menu (day, meal, item_name, restaurant_name)
VALUES (?, ?, ?, ?)
""", menus)

# ---------------------------
# 7. Seed Example Residents
# ---------------------------
token1 = seed_resident("Franco Patrick", "111", "device1_token.txt")
token2 = seed_resident("Angelo Antenor", "212", "device2_token.txt")

# ---------------------------
# Commit & Close
# ---------------------------
conn.commit()
conn.close()

print("Hotel database seeded successfully!")
