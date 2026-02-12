import sqlite3

conn = sqlite3.connect("queueless.db")
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS districts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_name TEXT UNIQUE
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS panchayats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        district_id INTEGER,
        panchayat_name TEXT,
        FOREIGN KEY (district_id) REFERENCES districts(id)
    )
""")

cur.execute("""
    CREATE TABLE IF NOT EXISTS wards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        panchayat_id INTEGER,
        ward_name TEXT,
        FOREIGN KEY (panchayat_id) REFERENCES panchayats(id)
    )
""")

conn.commit()
conn.close()

print("MASTER TABLES CREATED!")
