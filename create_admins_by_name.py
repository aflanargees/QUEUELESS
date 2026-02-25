import sqlite3
import re

conn = sqlite3.connect("queueless.db")
cur = conn.cursor()

rows = cur.execute("SELECT id, panchayat_name FROM panchayats").fetchall()

count = 0

for pid, name in rows:
    clean = name.strip().lower()
    clean = re.sub(r'\s+', '_', clean)      # Replace spaces with _
    clean = re.sub(r'[^a-z0-9_]', '', clean) # Remove special chars

    username = f"{clean}_admin"
    password = "1234"

    try:
        cur.execute("""
            INSERT INTO panchayat_admins (username, password, panchayat_id)
            VALUES (?, ?, ?)
        """, (username, password, pid))

        count += 1
    except Exception:
        pass  # skip duplicates

conn.commit()
conn.close()

print(f"Created {count} name-based panchayat admin accounts!")