import sqlite3

DB_NAME = "secretary.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    db = connect()

    db.execute("""
        CREATE TABLE IF NOT EXISTS replies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            button_text TEXT,
            button_url TEXT
        )
    """)

    db.commit()
    db.close()


def add_reply(question, answer, button_text=None, button_url=None):
    db = connect()

    db.execute(
        """
        INSERT INTO replies
        (question, answer, button_text, button_url)
        VALUES (?, ?, ?, ?)
        """,
        (question, answer, button_text, button_url)
    )

    db.commit()
    db.close()


def get_replies():
    db = connect()

    cursor = db.execute("""
        SELECT id, question, answer, button_text, button_url
        FROM replies
        ORDER BY id DESC
    """)

    data = cursor.fetchall()

    db.close()

    return data


def get_reply(reply_id):
    db = connect()

    cursor = db.execute("""
        SELECT id, question, answer, button_text, button_url
        FROM replies
        WHERE id = ?
    """, (reply_id,))

    data = cursor.fetchone()

    db.close()

    return data


def delete_reply(reply_id):
    db = connect()

    cursor = db.execute(
        "DELETE FROM replies WHERE id = ?",
        (reply_id,)
    )

    deleted = cursor.rowcount > 0

    db.commit()
    db.close()

    return deleted
