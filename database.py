import sqlite3
import time

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# ===== USERS =====
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0,
    invited_by INTEGER,
    created_at INTEGER
)
""")

# ===== REF TRACK (one-time credit) =====
cur.execute("""
CREATE TABLE IF NOT EXISTS referrals (
    user_id INTEGER PRIMARY KEY,
    referrer_id INTEGER
)
""")

# ===== TASKS =====
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    title TEXT,
    link TEXT,
    reward INTEGER,
    max_workers INTEGER,
    done_count INTEGER DEFAULT 0,
    active INTEGER DEFAULT 1
)
""")

# ===== TASK DONE =====
cur.execute("""
CREATE TABLE IF NOT EXISTS task_done (
    user_id INTEGER,
    task_id INTEGER,
    PRIMARY KEY (user_id, task_id)
)
""")

# ===== WITHDRAWS =====
cur.execute("""
CREATE TABLE IF NOT EXISTS withdraws (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    method TEXT,
    address TEXT,
    status TEXT DEFAULT 'pending',
    created_at INTEGER
)
""")

conn.commit()

# ================= USERS =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE user_id=?", (uid,))
    u = cur.fetchone()
    if not u:
        cur.execute(
            "INSERT INTO users (user_id, points, last_bonus, invited_by, created_at) VALUES (?,?,?,?,?)",
            (uid, 0, 0, None, int(time.time()))
        )
        conn.commit()
        return (uid, 0, 0, None, int(time.time()))
    return u

def add_points(uid, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, uid))
    conn.commit()

def set_bonus(uid):
    cur.execute("UPDATE users SET last_bonus=? WHERE user_id=?", (int(time.time()), uid))
    conn.commit()

def set_ref(user_id, referrer_id):
    # once per user
    cur.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,))
    if cur.fetchone():
        return False
    cur.execute("INSERT INTO referrals (user_id, referrer_id) VALUES (?,?)", (user_id, referrer_id))
    conn.commit()
    return True

# ================= TASKS =================
def add_task(owner, title, link, reward, max_workers):
    cur.execute(
        "INSERT INTO tasks (owner_id, title, link, reward, max_workers) VALUES (?,?,?,?,?)",
        (owner, title, link, reward, max_workers)
    )
    conn.commit()

def get_active_tasks(limit=20):
    cur.execute("""
    SELECT * FROM tasks
    WHERE active=1 AND done_count < max_workers
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    return cur.fetchall()

def mark_done(uid, task_id):
    try:
        cur.execute("INSERT INTO task_done (user_id, task_id) VALUES (?,?)", (uid, task_id))
        cur.execute("UPDATE tasks SET done_count = done_count + 1 WHERE id=?", (task_id,))
        conn.commit()
        return True
    except:
        return False

def is_done(uid, task_id):
    cur.execute("SELECT 1 FROM task_done WHERE user_id=? AND task_id=?", (uid, task_id))
    return cur.fetchone() is not None

def get_task(task_id):
    cur.execute("SELECT * FROM tasks WHERE id=?", (task_id,))
    return cur.fetchone()

# ================= WITHDRAW =================
def create_withdraw(uid, amount, method, address):
    cur.execute("""
    INSERT INTO withdraws (user_id, amount, method, address, created_at)
    VALUES (?,?,?,?,?)
    """, (uid, amount, method, address, int(time.time())))
    conn.commit()

def get_pending_withdraws():
    cur.execute("SELECT * FROM withdraws WHERE status='pending' ORDER BY id DESC")
    return cur.fetchall()

def set_withdraw_status(wid, status):
    cur.execute("UPDATE withdraws SET status=? WHERE id=?", (status, wid))
    conn.commit()
