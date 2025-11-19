import sqlite3

conn = sqlite3.connect("pushup_challenge.db")
cur = conn.cursor()
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("challenge_start", "2025-11-17"))
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("challenge_days", "100"))
cur.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", ("daily_target", "100"))
conn.commit()
conn.close()
print("Настройки записаны!")
