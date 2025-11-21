# seed_residents.py
import sqlite3
import uuid

conn = sqlite3.connect("data\hotel.db")
cursor = conn.cursor()

residents = [
    ("Franco Patrick", 101),
    ("Alice Vega", 102),
    ("Miguel Santos", 103),
    ("Sarah Lim", 104)
]

for name, room in residents:
    token = str(uuid.uuid4())
    cursor.execute("""
        INSERT OR IGNORE INTO residents (name, room_number, device_token)
        VALUES (?, ?, ?)
    """, (name, room, token))

    print(f"Seeded {name} | Room {room} | Token: {token}")

conn.commit()
conn.close()
