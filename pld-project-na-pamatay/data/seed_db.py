import sqlite3
import os
import uuid
import datetime

DB_PATH = os.path.join("data", "hotel.db")
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

def seed_resident(name, room_number):
    token = str(uuid.uuid4())
    checkin_time = datetime.datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO residents (name, room_number, device_token, checkin_time)
        VALUES (?, ?, ?, ?)
    """, (name, room_number, token, checkin_time))

    print(f"Seeded Resident -> {name} | Room {room_number}")
    print(f"Token: {token}\n")
    return token

def register_device_token(token):
    with open("device_token.txt", "w") as f:
        f.write(token)
    print("Token stored on device.")

# ---------------------------
# Buildings
# ---------------------------

cursor.execute("INSERT OR IGNORE INTO buildings (name) VALUES (?)", ("Dionysus",))
cursor.execute("SELECT building_id FROM buildings WHERE name=?", ("Dionysus",))
dionysus_id = cursor.fetchone()[0]

# ---------------------------
# Wings
# ---------------------------

cursor.execute("""
INSERT OR IGNORE INTO wings (building_id, name, wifi_ssid, wifi_password)
VALUES (?, ?, ?, ?)
""", (dionysus_id, "Right", "DRWifi", "LoBxeen"))

cursor.execute("""
INSERT OR IGNORE INTO wings (building_id, name, wifi_ssid, wifi_password)
VALUES (?, ?, ?, ?)
""", (dionysus_id, "Left", "DLWifi", "PoTroox"))

# Function to get wing_id
def get_wing_id(wing_name):
    cursor.execute("SELECT wing_id FROM wings WHERE name=?", (wing_name,))
    return cursor.fetchone()[0]

right_wing_id = get_wing_id("Right")
left_wing_id = get_wing_id("Left")

# ---------------------------
# Rooms
# ---------------------------

# Right Wing
right_tv_brands = ["Samsung", "LG", "Sony", "Panasonic", "TCL"]
right_fans = ["Ceiling Fan", "Tower Fan", "Ceiling Fan", "Tower Fan", "Ceiling Fan"]
right_thermostats = ["Nest V3", "Honeywell T6", "Nest V3", "Honeywell T6", "Nest V3"]

for i, room_number in enumerate([101, 102, 103, 104, 105, 201, 202, 203, 204, 205]):
    idx = i % 5
    cursor.execute("""
        INSERT OR IGNORE INTO rooms (room_number, building_id, wing_id, tv_brand, fan_type, thermostat_model)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(room_number), dionysus_id, right_wing_id,
          right_tv_brands[idx], right_fans[idx], right_thermostats[idx]))

# Left Wing
left_tv_brands = ["Sony", "TCL", "LG", "Samsung", "Panasonic"]
left_fans = ["Tower Fan", "Ceiling Fan", "Tower Fan", "Ceiling Fan", "Tower Fan"]
left_thermostats = ["Honeywell T6", "Nest V3", "Honeywell T6", "Nest V3", "Honeywell T6"]

for i, room_number in enumerate([106, 107, 108, 109, 110, 206, 207, 208, 209, 210]):
    idx = i % 5
    cursor.execute("""
        INSERT OR IGNORE INTO rooms (room_number, building_id, wing_id, tv_brand, fan_type, thermostat_model)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (str(room_number), dionysus_id, left_wing_id,
          left_tv_brands[idx], left_fans[idx], left_thermostats[idx]))

# ---------------------------
# Amenities
# ---------------------------

amenities = [
    (dionysus_id, "Housekeeping", "Daily room cleaning service", 1),
    (dionysus_id, "Communal Restroom", "Restrooms for guests on each floor", 1)
]

cursor.executemany("""
INSERT OR IGNORE INTO amenities (building_id, name, description, floor)
VALUES (?, ?, ?, ?)
""", amenities)

# ---------------------------
# Pools
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
# Activity Center
# ---------------------------

activities = [
    (1, "indoor_board", "Chess"),
    (1, "indoor_board", "Table Soccer"),
    (1, "indoor_board", "Air Hockey"),
    (2, "indoor_sports", "Table Tennis"),
    (2, "indoor_sports", "Darts")
]

cursor.executemany("""
INSERT OR IGNORE INTO activity_center (floor, type, activity_name)
VALUES (?, ?, ?)
""", activities)

# ---------------------------
# Restaurant Menu
# ---------------------------

menus = [
    # Breakfast Buffets
    ("Monday", "Breakfast", "Breakfast Buffet"),
    ("Thursday", "Breakfast", "Breakfast Buffet"),
    ("Sunday", "Breakfast", "Breakfast Buffet"),

    # Brunch Buffets
    ("Tuesday", "Brunch", "Brunch Buffet"),
    ("Friday", "Brunch", "Brunch Buffet"),

    # Lunch items
    ("Monday", "Lunch", "Grilled Chicken Salad"),
    ("Monday", "Lunch", "Vegetable Stir Fry"),

    ("Tuesday", "Lunch", "Beef Burger"),
    ("Tuesday", "Lunch", "Quinoa Bowl"),

    ("Wednesday", "Lunch", "Spaghetti Bolognese"),
    ("Wednesday", "Lunch", "Caesar Salad"),

    ("Thursday", "Lunch", "Chicken Alfredo"),
    ("Thursday", "Lunch", "Garden Salad"),

    ("Friday", "Lunch", "Fish & Chips"),
    ("Friday", "Lunch", "Vegetable Curry"),

    ("Saturday", "Lunch", "Pasta Primavera"),
    ("Saturday", "Lunch", "Chicken Caesar Wrap"),

    ("Sunday", "Lunch", "Roast Beef Sandwich"),
    ("Sunday", "Lunch", "Caprese Salad")
]

cursor.executemany("""
INSERT OR IGNORE INTO restaurant_menu (day, meal, item_name)
VALUES (?, ?, ?)
""", menus)

tokenid = seed_resident("Franco Patrick", "101")
tokenid = seed_resident("Angelo Antenor", "106")
register_device_token(tokenid)


# ---------------------------
# Commit and close
# ---------------------------
conn.commit()
conn.close()

print("Hotel database seeded successfully!")
