import sqlite3
import time

conn = sqlite3.connect("platform.db", check_same_thread=False)
cur = conn.cursor()

# USERS
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    points INTEGER DEFAULT 0,
    referrer INTEGER,
    created_at INTEGER
)
""")

# TASKS / MARKETPLACE
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

# ADS
cur.execute("""
CREATE TABLE IF NOT EXISTS ads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    content TEXT,
    cost INTEGER,
    duration INTEGER,
    active INTEGER DEFAULT 1
)
""")

# WITHDRAWALS
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

# ===== USERS =====
def get_user(uid, username=None):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cur.fetchone()

    if not u:
        cur.execute(
            "INSERT INTO users VALUES (?,?,?,?,?)",
            (uid, username, 0, None, int(time.time()))
        )
        conn.commit()
        return (uid, username, 0, None, int(time.time()))

    if username:
        cur.execute("UPDATE users SET username=? WHERE user_id=?", (username, uid))
        conn.commit()

    return u

def add_points(uid, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, uid))
    conn.commit()

# ===== TASKS =====
def add_task(uid, title, link, reward, budget):
    cur.execute(
        "INSERT INTO tasks (owner_id,title,link,reward,budget,remaining) VALUES (?,?,?,?,?,?)",
        (uid, title, link, reward, budget, budget)
    )
    conn.commit()

def get_tasks():
    cur.execute("SELECT * FROM tasks WHERE remaining > 0")
    return cur.fetchall()

def use_task(task_id):
    cur.execute("UPDATE tasks SET remaining = remaining - 1 WHERE id=?", (task_id,))
    conn.commit()
