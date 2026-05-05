import sqlite3
import time

# ================= DB INIT =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# ================= TABLES =================
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    ref INTEGER DEFAULT 0,
    last_bonus INTEGER DEFAULT 0,
    username TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER,
    title TEXT,
    reward INTEGER
)
""")

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

cur.execute("""
CREATE TABLE IF NOT EXISTS bonus_links (
    code TEXT PRIMARY KEY,
    used INTEGER DEFAULT 0
)
""")

conn.commit()

# ================= USERS =================
def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users (user_id, points, last_bonus, username) VALUES (?,0,0,'')",
            (user_id,)
        )
        conn.commit()

        return (user_id, 0, 0, 0, "")

    return user


def add_points(user_id, amount):
    cur.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()


def set_bonus(user_id):
    cur.execute(
        "UPDATE users SET last_bonus=? WHERE user_id=?",
        (int(time.time()), user_id)
    )
    conn.commit()


# ================= TASKS =================
def add_task(owner_id, title, reward):
    cur.execute(
        "INSERT INTO tasks (owner_id, title, reward) VALUES (?,?,?)",
        (owner_id, title, reward)
    )
    conn.commit()


def get_tasks():
    cur.execute("SELECT * FROM tasks")
    return cur.fetchall()


# ================= WITHDRAW =================
def create_withdraw(user_id, amount, method, address):
    cur.execute(
        "INSERT INTO withdraws (user_id, amount, method, address) VALUES (?,?,?,?)",
        (user_id, amount, method, address)
    )
    conn.commit()


def get_withdraws():
    cur.execute("SELECT * FROM withdraws")
    return cur.fetchall()


# ================= BONUS LINKS =================
def save_bonus(code):
    cur.execute(
        "INSERT INTO bonus_links (code) VALUES (?)",
        (code,)
    )
    conn.commit()


# ================= USER SEARCH =================
def get_user_by_username(username):
    cur.execute(
        "SELECT * FROM users WHERE username=?",
        (username,)
    )
    return cur.fetchone()


# ================= OPTIONAL: UPDATE USERNAME =================
def update_username(user_id, username):
    cur.execute(
        "UPDATE users SET username=? WHERE user_id=?",
        (username, user_id)
    )
    conn.commit()
