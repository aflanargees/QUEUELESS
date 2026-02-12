import sqlite3
import csv

conn = sqlite3.connect("queueless.db")
cur = conn.cursor()

# LOAD DISTRICTS
with open("C:/Users/AFLA MUTHALIB/mini project/QUEUELESS/districts.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        cur.execute("INSERT OR IGNORE INTO districts (district_name) VALUES (?)", (row[0],))

# LOAD PANCHAYATS
with open("C:/Users/AFLA MUTHALIB/mini project/QUEUELESS/panchayats.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for district_name, panchayat in reader:
        cur.execute("SELECT id FROM districts WHERE district_name=?", (district_name,))
        res = cur.fetchone()
        if res:
            dist_id = res[0]
            cur.execute(
                "INSERT OR IGNORE INTO panchayats (district_id, panchayat_name) VALUES (?,?)",
                (dist_id, panchayat)
            )

# LOAD WARDS
with open("C:/Users/AFLA MUTHALIB/mini project/QUEUELESS/wards.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    next(reader)
    for district_name, panchayat, ward in reader:

        cur.execute("SELECT id FROM districts WHERE district_name=?", (district_name,))
        dist_res = cur.fetchone()
        if not dist_res:
            continue
        dist_id = dist_res[0]

        cur.execute(
            "SELECT id FROM panchayats WHERE panchayat_name=? AND district_id=?",
            (panchayat, dist_id)
        )
        p_res = cur.fetchone()
        if not p_res:
            continue
        p_id = p_res[0]

        cur.execute(
            "INSERT OR IGNORE INTO wards (panchayat_id, ward_name) VALUES (?, ?)",
            (p_id, ward)
        )

conn.commit()
conn.close()
print("Data imported successfully!")

