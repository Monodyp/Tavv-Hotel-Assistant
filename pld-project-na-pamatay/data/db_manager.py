import sqlite3
import os
import datetime
import uuid

DB_PATH = os.path.join("data", "hotel.db")
os.makedirs("data", exist_ok=True)


class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    def connect(self):
        return sqlite3.connect(self.db_path)

    # ---------------------------
    # 0. Residents CRUD
    # ---------------------------
    def add_resident(self, name, room_number):
        token = str(uuid.uuid4())
        checkin_time = datetime.datetime.now().isoformat()
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO residents (name, room_number, device_token, checkin_time)
            VALUES (?, ?, ?, ?)
        """, (name, room_number, token, checkin_time))
        conn.commit()
        conn.close()
        print(f"Resident added: {name} | Room {room_number} | Token: {token}")

    def delete_resident(self, resident_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM residents WHERE resident_id=?", (resident_id,))
        conn.commit()
        conn.close()
        print(f"Resident {resident_id} deleted.")

    def list_residents(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT resident_id, name, room_number, device_token FROM residents")
        rows = cursor.fetchall()
        conn.close()
        return rows

    # ---------------------------
    # 1. Buildings CRUD
    # ---------------------------
    def add_building(self, name):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO buildings (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        print(f"Building added: {name}")

    def list_buildings(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT building_id, name FROM buildings")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_building(self, building_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM buildings WHERE building_id=?", (building_id,))
        conn.commit()
        conn.close()
        print(f"Building {building_id} deleted.")

    # ---------------------------
    # 2. Wings CRUD
    # ---------------------------
    def add_wing(self, building_id, name, wifi_ssid, wifi_password):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO wings (building_id, name, wifi_ssid, wifi_password)
            VALUES (?, ?, ?, ?)
        """, (building_id, name, wifi_ssid, wifi_password))
        conn.commit()
        conn.close()
        print(f"Wing added: {name} in building {building_id}")

    def list_wings(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT wing_id, building_id, name, wifi_ssid FROM wings")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_wing(self, wing_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM wings WHERE wing_id=?", (wing_id,))
        conn.commit()
        conn.close()
        print(f"Wing {wing_id} deleted.")

    # ---------------------------
    # 3. Rooms CRUD
    # ---------------------------
    def add_room(self, room_number, building_id, wing_id, tv_brand="", fan_type="", thermostat_model=""):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO rooms (room_number, building_id, wing_id, tv_brand, fan_type, thermostat_model)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (room_number, building_id, wing_id, tv_brand, fan_type, thermostat_model))
        conn.commit()
        conn.close()
        print(f"Room added: {room_number}")

    def list_rooms(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT room_number, building_id, wing_id FROM rooms")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_room(self, room_number):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM rooms WHERE room_number=?", (room_number,))
        conn.commit()
        conn.close()
        print(f"Room {room_number} deleted.")

    # ---------------------------
    # 4. Amenities CRUD
    # ---------------------------
    def add_amenity(self, building_id, name, description, floor):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO amenities (building_id, name, description, floor)
            VALUES (?, ?, ?, ?)
        """, (building_id, name, description, floor))
        conn.commit()
        conn.close()
        print(f"Amenity added: {name} (Floor {floor})")

    def list_amenities(self):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("SELECT amenity_id, building_id, name, floor FROM amenities")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def delete_amenity(self, amenity_id):
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM amenities WHERE amenity_id=?", (amenity_id,))
        conn.commit()
        conn.close()
        print(f"Amenity {amenity_id} deleted.")

    # ---------------------------
    # Add more CRUD methods for Pools, Activity Center, Restaurant Menu similarly
    # ---------------------------

# ---------------------------
# Terminal UI
# ---------------------------

def main_menu():
    db = DatabaseManager()
    while True:
        print("\n=== Hotel DB Manager ===")
        print("1. Add Resident")
        print("2. List Residents")
        print("3. Delete Resident")
        print("4. Add Building")
        print("5. List Buildings")
        print("6. Delete Building")
        print("7. Add Wing")
        print("8. List Wings")
        print("9. Delete Wing")
        print("10. Add Room")
        print("11. List Rooms")
        print("12. Delete Room")
        print("13. Add Amenity")
        print("14. List Amenities")
        print("15. Delete Amenity")
        print("0. Exit")

        choice = input("Enter choice: ")

        if choice == "1":
            name = input("Resident name: ")
            room = input("Room number: ")
            db.add_resident(name, room)
        elif choice == "2":
            for r in db.list_residents():
                print(r)
        elif choice == "3":
            rid = int(input("Resident ID to delete: "))
            db.delete_resident(rid)
        elif choice == "4":
            name = input("Building name: ")
            db.add_building(name)
        elif choice == "5":
            for b in db.list_buildings():
                print(b)
        elif choice == "6":
            bid = int(input("Building ID to delete: "))
            db.delete_building(bid)
        elif choice == "7":
            bid = int(input("Building ID: "))
            name = input("Wing name: ")
            ssid = input("WiFi SSID: ")
            pwd = input("WiFi Password: ")
            db.add_wing(bid, name, ssid, pwd)
        elif choice == "8":
            for w in db.list_wings():
                print(w)
        elif choice == "9":
            wid = int(input("Wing ID to delete: "))
            db.delete_wing(wid)
        elif choice == "10":
            rn = input("Room number: ")
            bid = int(input("Building ID: "))
            wid = int(input("Wing ID: "))
            tv = input("TV Brand: ")
            fan = input("Fan Type: ")
            thermo = input("Thermostat Model: ")
            db.add_room(rn, bid, wid, tv, fan, thermo)
        elif choice == "11":
            for r in db.list_rooms():
                print(r)
        elif choice == "12":
            rn = input("Room number to delete: ")
            db.delete_room(rn)
        elif choice == "13":
            bid = int(input("Building ID: "))
            name = input("Amenity name: ")
            desc = input("Description: ")
            floor = int(input("Floor: "))
            db.add_amenity(bid, name, desc, floor)
        elif choice == "14":
            for a in db.list_amenities():
                print(a)
        elif choice == "15":
            aid = int(input("Amenity ID to delete: "))
            db.delete_amenity(aid)
        elif choice == "0":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main_menu()
