import sqlite3
from datetime import datetime , timedelta

def get_challenge_status():
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()

    # Параметры челленджа
    cur.execute("SELECT value FROM settings WHERE key = 'challenge_start'")
    challenge_start = cur.fetchone()
    if challenge_start:
        challenge_start = challenge_start[0]
    else:
        challenge_start = "2025-11-17"
    cur.execute("SELECT value FROM settings WHERE key = 'challenge_days'")
    challenge_days = cur.fetchone()
    if challenge_days:
        challenge_days = int(challenge_days[0])
    else:
        challenge_days = 100
    cur.execute("SELECT value FROM settings WHERE key = 'daily_target'")
    daily_target = cur.fetchone()
    if daily_target:
        daily_target = int(daily_target[0])
    else:
        daily_target = 100

    # Даты
    date_start = datetime.strptime(challenge_start, "%Y-%m-%d")
    date_today = datetime.now()
    date_end = date_start + timedelta(days=challenge_days-1)
    days_total = (date_end - date_start).days + 1
    days_passed = (date_today - date_start).days + 1
    if days_passed < 1:
        days_passed = 1
    days_left = max(0, days_total - days_passed)

    # Количество участников
    cur.execute("SELECT COUNT(*) FROM participants")
    member_count = cur.fetchone()[0]

    # Сумма отжиманий за весь период
    cur.execute("""
        SELECT SUM(reps_done)
        FROM daily_stats
        WHERE date >= ? AND date <= ?
    """, (challenge_start, date_today.strftime("%Y-%m-%d")))
    total_reps = cur.fetchone()[0] or 0

    # Сколько должно быть сделано на сегодня по плану
    plan_reps = member_count * daily_target * days_passed

    # % выполнения
    percent = min(100, round(total_reps / plan_reps * 100, 1)) if plan_reps else 0

    # Кто всегда выполняет норму
    cur.execute("""
        SELECT p.username, p.full_name, p.custom_name
        FROM participants p
        WHERE NOT EXISTS (
            SELECT 1 FROM daily_stats d
            WHERE p.telegram_id = d.telegram_id
            AND d.date >= ?
            AND d.date <= ?
            AND d.completed = 0
        )
    """, (challenge_start, date_today.strftime("%Y-%m-%d")))
    perfect = cur.fetchall()

    conn.close()

    return {
        "days_left": days_left,
        "days_total": days_total,
        "days_passed": days_passed,
        "total_reps": total_reps,
        "plan_reps": plan_reps,
        "percent": percent,
        "perfect_users": perfect,
        "date_end": date_end.strftime("%Y-%m-%d")
    }

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
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_reps(telegram_id, username, full_name, reps):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    # Добавить участника, если он новый
    cur.execute("INSERT OR IGNORE INTO participants VALUES (?, ?, ?)", (telegram_id, username, full_name))
    # Проверь, есть ли запись на сегодня
    cur.execute("SELECT reps_done FROM daily_stats WHERE telegram_id = ? AND date = ?", (telegram_id, today))
    row = cur.fetchone()
    if row:
        reps_done = row[0] + reps
        completed = int(reps_done >= 100)
        cur.execute("UPDATE daily_stats SET reps_done = ?, completed = ? WHERE telegram_id = ? AND date = ?",
                    (reps_done, completed, telegram_id, today))
    else:
        reps_done = reps
        completed = int(reps >= 100)
        cur.execute("INSERT INTO daily_stats (telegram_id, date, reps_done, completed) VALUES (?, ?, ?, ?)",
                    (telegram_id, today, reps, completed))
    conn.commit()
    conn.close()
    return reps_done, completed

def get_user_stats_today(telegram_id):
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT reps_done, completed
        FROM daily_stats
        WHERE telegram_id = ? AND date = ?
    """, (telegram_id, today))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], bool(row[1])
    return 0, False

def get_group_stats_today():
    today = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT p.username, p.full_name, p.custom_name, d.reps_done, d.completed
        FROM participants p
        LEFT JOIN daily_stats d ON p.telegram_id = d.telegram_id AND d.date = ?
        ORDER BY p.username, p.full_name, p.custom_name
    """, (today,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_user_stats_period(telegram_id, start, end):
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    cur.execute("""
        SELECT SUM(reps_done)
        FROM daily_stats
        WHERE telegram_id = ? AND date >= ? AND date <= ?
    """, (telegram_id, start, end))
    total = cur.fetchone()[0] or 0
    conn.close()
    return total

def get_group_stats_period(start, end):
    conn = sqlite3.connect("pushup_challenge.db")
    cur = conn.cursor()
    cur.execute("""
       SELECT p.username, p.full_name, p.custom_name, SUM(d.reps_done) AS total_done
        FROM participants p
        LEFT JOIN daily_stats d ON p.telegram_id = d.telegram_id AND d.date >= ? AND d.date <= ?
        GROUP BY p.telegram_id
        ORDER BY total_done DESC
    """, (start, end))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_display_name(username, full_name, custom_name):
    if custom_name and custom_name.strip():
        return custom_name
    if username and username.strip():
        return f"@{username}"
    if full_name and full_name.strip():
        return full_name
    return "Без имени"

