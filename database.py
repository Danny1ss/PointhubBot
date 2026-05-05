import sqlite3
import time

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

# ADS
cur.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT,
    status TEXT DEFAULT 'pending'
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

conn.commit()


# ================= USERS =================
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


def set_last_bonus(uid):
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (int(time.time()), uid))
    conn.commit()


# ================= ADS =================
def create_ad(uid, text):
    cur.execute("INSERT INTO ads (user_id, text) VALUES (?, ?)", (uid, text))
    conn.commit()


def get_ads():
    cur.execute("SELECT * FROM ads WHERE status='pending'")
    return cur.fetchall()


def update_ad(aid, status):
    cur.execute("UPDATE ads SET status=? WHERE id=?", (status, aid))
    conn.commit()


# ================= WITHDRAW =================
def create_withdraw(uid, amount, method, address):
    cur.execute("""
        INSERT INTO withdraws (user_id, amount, method, address)
        VALUES (?, ?, ?, ?)
    """, (uid, amount, method, address))
    conn.commit()


def get_withdraws():
    cur.execute("SELECT * FROM withdraws WHERE status='pending'")
    return cur.fetchall()


def update_withdraw(wid, status):
    cur.execute("UPDATE withdraws SET status=? WHERE id=?", (status, wid))
    conn.commit()
