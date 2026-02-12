import sqlite3

conn = sqlite3.connect("queueless.db")

conn.execute("""
CREATE TABLE IF NOT EXISTS districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_name TEXT UNIQUE
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS panchayats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER,
    panchayat_name TEXT,
    FOREIGN KEY (district_id) REFERENCES districts(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS wards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    panchayat_id INTEGER,
    ward_name TEXT,
    FOREIGN KEY (panchayat_id) REFERENCES panchayats(id)
)
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    district_id INTEGER,
    panchayat_id INTEGER,
    ward_id INTEGER,
    purpose TEXT,
    token_number INTEGER,
    counter_number INTEGER,
    status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()
conn.close()

print("Database & tables created successfully.")
