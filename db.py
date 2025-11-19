import sqlite3

def init_db():
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS participants (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS daily_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            date TEXT,
            reps_done INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            UNIQUE(telegram_id, date)
        )
    """)
    conn.commit()
    conn.close()

# Первый запуск (или пересоздать базу)
if __name__ == "__main__":
    init_db()
    print("Database initialized.")
