import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0
)
""")

# TASKS (Marketplace)
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    title TEXT,
    link TEXT,
    reward INTEGER,
    budget INTEGER,
    remaining INTEGER
)
""")

# DONE TASKS
cur.execute("""
CREATE TABLE IF NOT EXISTS done (
    user_id INTEGER,
    task_id INTEGER
)
""")

# ADS
cur.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    text TEXT,
    duration INTEGER,
    created_at INTEGER
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
def get_user(uid, username=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cur.fetchone()

    if not u:
        cur.execute("INSERT INTO users VALUES (?,?,0,0)", (uid, username))
        conn.commit()
        return (uid, username, 0, 0)

    if username:
        cur.execute("UPDATE users SET username=? WHERE user_id=?", (username, uid))
        conn.commit()

    return u


def add_points(uid, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, uid))
    conn.commit()


def set_bonus(uid):
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (int(time.time()), uid))
    conn.commit()


# ================= TASKS =================
def get_tasks():
    cur.execute("SELECT * FROM tasks WHERE remaining > 0")
    return cur.fetchall()


def mark_done(uid, tid):
    cur.execute("INSERT INTO done VALUES (?,?)", (uid, tid))
    conn.commit()


def is_done(uid, tid):
    cur.execute("SELECT * FROM done WHERE user_id=? AND task_id=?", (uid, tid))
    return cur.fetchone()


# ================= WITHDRAW =================
def get_withdraws():
    cur.execute("SELECT * FROM withdraws WHERE status='pending'")
    return cur.fetchall()


def update_withdraw(wid, status):
    cur.execute("UPDATE withdraws SET status=? WHERE id=?", (status, wid))
    conn.commit()


# ================= ADS =================
def get_ads():
    cur.execute("SELECT * FROM ads ORDER BY id DESC")
    return cur.fetchall()
