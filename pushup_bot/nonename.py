import sqlite3

conn = sqlite3.connect("pushup_challenge.db")
cur = conn.cursor()
cur.execute("""
    UPDATE participants
    SET custom_name = ?
    WHERE telegram_id = ?
""", ("Евген", 358478324))
conn.commit()
conn.close()
print("Имя 'Евген' успешно присвоено пользователю с ID 358478324!")