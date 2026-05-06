import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# ===== USERS =====
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0
)
""")

# ===== TASKS =====
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    text TEXT,
    reward INTEGER
)
""")

# ===== TASK DONE =====
cur.execute("""
CREATE TABLE IF NOT EXISTS task_done (
    user_id INTEGER,
    task_id INTEGER
)
""")

conn.commit()

# ================= USERS =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    user = cur.fetchone()

    if not user:
        cur.execute("INSERT INTO users (user_id, points, last_bonus) VALUES (?,0,0)", (uid,))
        conn.commit()
        return (uid, 0, 0)

    return user


def add_points(uid, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, uid))
    conn.commit()


def set_bonus(uid):
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (int(time.time()), uid))
    conn.commit()

# ================= TASKS =================
def add_task(owner, text, reward):
    cur.execute("INSERT INTO tasks (owner_id, text, reward) VALUES (?,?,?)", (owner, text, reward))
    conn.commit()


def get_tasks():
    cur.execute("SELECT * FROM tasks")
    return cur.fetchall()


def is_done(uid, task_id):
    cur.execute("SELECT * FROM task_done WHERE user_id=? AND task_id=?", (uid, task_id))
    return cur.fetchone()


def mark_done(uid, task_id):
    cur.execute("INSERT INTO task_done (user_id, task_id) VALUES (?,?)", (uid, task_id))
    conn.commit()
