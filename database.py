import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0
)
""")

# WITHDRAW
cur.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    method TEXT,
    address TEXT,
    status TEXT DEFAULT 'pending'
)
""")

# ADS
cur.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()


def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cur.fetchone()

    if not u:
        cur.execute("INSERT INTO users (user_id) VALUES (?)", (uid,))
        conn.commit()
        return (uid, 0, 0, 0)

    return u


def add_points(uid, p):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (p, uid))
    conn.commit()


def create_withdraw(uid, amount, method, address):
    cur.execute("""
        INSERT INTO withdraws (user_id, amount, method, address)
        VALUES (?, ?, ?, ?)
    """, (uid, amount, method, address))
    conn.commit()


def get_pending_withdraws():
    cur.execute("SELECT * FROM withdraws WHERE status='pending'")
    return cur.fetchall()


def update_withdraw(id, status):
    cur.execute("UPDATE withdraws SET status=? WHERE id=?", (status, id))
    conn.commit()


def create_ad(uid, text):
    cur.execute("INSERT INTO ads (user_id, text) VALUES (?, ?)", (uid, text))
    conn.commit()


def get_ads():
    cur.execute("SELECT * FROM ads WHERE status='pending'")
    return cur.fetchall()


def update_ad(id, status):
    cur.execute("UPDATE ads SET status=? WHERE id=?", (status, id))
    conn.commit()
