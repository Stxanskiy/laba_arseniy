import sqlite3

def init_db():
    conn = sqlite3.connect("finance_manager.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        role TEXT CHECK(role IN ('admin', 'user')),
        secret_question TEXT,
        secret_answer TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        type TEXT CHECK(type IN ('income', 'expense')),
        amount REAL,
        category TEXT,
        date TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        type TEXT CHECK(type IN ('income', 'expense'))
    )
    """)

    cursor.execute("""
            INSERT OR IGNORE INTO users (username, password, role)
            VALUES ('admin', '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd3e4e6f89', 'admin')
        """)  # Пароль: 'password', зашифрованный через sha256

    conn.commit()
    conn.close()
