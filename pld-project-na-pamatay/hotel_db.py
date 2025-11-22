import sqlite3
from datetime import datetime

DB_PATH = "data/hotel.db"

class DatabaseLoader:

    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    # -----------------------
    # TOKEN → RESIDENT LOOKUP
    # -----------------------
    def get_resident_from_token(self, token):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT resident_id, name, room_number, device_token, checkin_time, checkout_time, token_voided
            FROM residents
            WHERE device_token = ? AND token_voided = 0
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
            "checkin_time": row[4],
            "checkout_time": row[5],
            "token_voided": bool(row[6])
        }

    # -----------------------
    # FULL CONTEXT (ROOM)
    # -----------------------
    def get_full_context(self, room_number: str):

        conn = self.connect()
        cursor = conn.cursor()

        # 0. Resident info (active only)
        cursor.execute("""
            SELECT resident_id, name, room_number, device_token, checkin_time
            FROM residents
            WHERE room_number = ? AND token_voided = 0
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

        # 1. Room + building
        cursor.execute("""
            SELECT 
                r.room_number,
                r.tv_brand,
                r.fan_type,
                r.thermostat_model,
                r.floor,
                r.room_type,
                b.building_id,
                b.name AS building_name,
                b.wifi_ssid,
                b.wifi_password,
                b.restaurant_name
            FROM rooms r
            JOIN buildings b ON r.building_id = b.building_id
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
            floor,
            room_type,
            building_id,
            building_name,
            wifi_ssid,
            wifi_password,
            restaurant_name
        ) = room

        # 2. Amenities
        cursor.execute("""
            SELECT name, description, floor
            FROM amenities
            WHERE building_id = ?
        """, (building_id,))
        amenities = cursor.fetchall()

        # 3. Water sports activities
        cursor.execute("SELECT name, description FROM water_sports")
        water_sports = cursor.fetchall()

        # 4. Pools
        cursor.execute("SELECT name, features FROM pools")
        pools = cursor.fetchall()

        # 5. Restaurant menu (Island Cafe only)
        today_day = datetime.now().strftime("%A")
        cursor.execute("""
            SELECT day, meal, item_name
            FROM restaurant_menu
            WHERE restaurant_name = ? AND day = ?
            ORDER BY meal, item_name
        """, (restaurant_name, today_day))
        menu = cursor.fetchall()

        conn.close()

        return {
            "resident": resident_info,
            "room": {
                "room_number": room_number,
                "tv_brand": tv_brand,
                "fan_type": fan_type,
                "thermostat_model": thermostat_model,
                "floor": floor,
                "room_type": room_type
            },
            "building": {
                "id": building_id,
                "name": building_name,
                "wifi_ssid": wifi_ssid,
                "wifi_password": wifi_password,
                "restaurant_name": restaurant_name
            },
            "amenities": [
                {"name": a[0], "description": a[1], "floor": a[2]} for a in amenities
            ],
            "water_sports": [
                {"name": ws[0], "description": ws[1]} for ws in water_sports
            ],
            "pools": [
                {"name": p[0], "features": p[1]} for p in pools
            ],
            "restaurant_menu": [
                {"day": m[0], "meal": m[1], "item_name": m[2]} for m in menu
            ]
        }
