import sqlite3

conn = sqlite3.connect("queueless.db")
cur = conn.cursor()

counters = ["Counter 1", "Counter 2", "Counter 3"]

for c in counters:
    cur.execute("INSERT INTO counters(counter_name, is_active) VALUES (?, 0)", (c,))

conn.commit()
conn.close()
print("Counters inserted")