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
    last_bonus INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0
)
""")

# TASKS
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    link TEXT,
    reward INTEGER,
    status TEXT DEFAULT 'active'
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
        return (uid, 0, 0, 0, 0)
    return u


def add_points(uid, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, uid))
    conn.commit()


def set_vip(uid, level):
    cur.execute("UPDATE users SET vip=? WHERE user_id=?", (level, uid))
    conn.commit()


def set_bonus(uid):
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (int(time.time()), uid))
    conn.commit()

# ================= TASKS =================
def add_task(owner, link, reward):
    cur.execute("INSERT INTO tasks (owner_id, link, reward) VALUES (?, ?, ?)", (owner, link, reward))
    conn.commit()


def get_tasks():
    cur.execute("SELECT * FROM tasks WHERE status='active'")
    return cur.fetchall()


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
