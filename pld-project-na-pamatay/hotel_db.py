import sqlite3
from datetime import datetime

DB_PATH = "data/hotel.db"

class DatabaseLoader:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    # -----------------------
    # TOKEN → ROOM LOOKUP
    # -----------------------
    def get_resident_from_token(self, token):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT resident_id, name, room_number, device_token, checkin_time
            FROM residents
            WHERE device_token = ?
        """, (token,))
    
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return {
            "resident_id": row[0],
            "name": row[1],
            "room_number": row[2],
            "device_token": row[3],
            "checkin_time": row[4]
        }

    # -----------------------
    # FULL CONTEXT (ROOM)
    # -----------------------
    def get_full_context(self, room_number: str):

        conn = self.connect()
        cursor = conn.cursor()

        # 0. Resident info
        cursor.execute("""
            SELECT resident_id, name, room_number, device_token, checkin_time
            FROM residents
            WHERE room_number = ?
        """, (room_number,))
        resident = cursor.fetchone()

        if resident:
            resident_info = {
                "resident_id": resident[0],
                "resident_name": resident[1],
                "resident_room": resident[2],
                "resident_device_token": resident[3],
                "resident_checkin_time": resident[4]
            }
        else:
            resident_info = None

        # 1. Room + building + wing
        cursor.execute("""
        SELECT 
            r.room_number,
            r.tv_brand,
            r.fan_type,
            r.thermostat_model,
            b.building_id,
            b.name AS building_name,
            w.wing_id,
            w.name AS wing_name,
            w.wifi_ssid,
            w.wifi_password
        FROM rooms r
        JOIN buildings b ON r.building_id = b.building_id
        JOIN wings w ON r.wing_id = w.wing_id
        WHERE r.room_number = ?
        """, (room_number,))
        room = cursor.fetchone()

        if not room:
            conn.close()
            return {"error": f"Room {room_number} not found."}

        (
            room_number,
            tv_brand,
            fan_type,
            thermostat_model,
            building_id,
            building_name,
            wing_id,
            wing_name,
            wifi_ssid,
            wifi_password
        ) = room

        # 2. Amenities
        cursor.execute("""
            SELECT name, description, floor
            FROM amenities
            WHERE building_id = ?
        """, (building_id,))
        amenities = cursor.fetchall()

        # 3. Activities
        cursor.execute("SELECT floor, type, activity_name FROM activity_center")
        activities = cursor.fetchall()

        # 4. Pools
        cursor.execute("SELECT name, features FROM pools")
        pools = cursor.fetchall()

        # 5. Restaurant menu
        today_day = datetime.now().strftime("%A")
        cursor.execute("""
            SELECT day, meal, item_name
            FROM restaurant_menu
            WHERE day = ?
            ORDER BY meal, item_name
        """, (today_day,))
        menu = cursor.fetchall()

        conn.close()

        return {
            "resident": resident_info,
            "room": {
                "room_number": room_number,
                "tv_brand": tv_brand,
                "fan_type": fan_type,
                "thermostat_model": thermostat_model,
            },
            "building": {
                "id": building_id,
                "name": building_name,
            },
            "wing": {
                "id": wing_id,
                "name": wing_name,
                "wifi_ssid": wifi_ssid,
                "wifi_password": wifi_password
            },
            "amenities": [
                {"name": a[0], "description": a[1], "floor": a[2]} for a in amenities
            ],
            "activities": [
                {"floor": act[0], "type": act[1], "name": act[2]} for act in activities
            ],
            "pools": [
                {"name": p[0], "features": p[1]} for p in pools
            ],
            "restaurant_menu": [
                {"day": m[0], "meal": m[1], "item_name": m[2]} for m in menu
            ]
        }
