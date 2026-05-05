import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# USERS
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0,
    invited_by INTEGER
)
""")

# WITHDRAWALS
cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# ======================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return (user_id, 0, 0, 0, None)

    return user


def add_points(user_id, amount):
    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()


def get_points(user_id):
    return get_user(user_id)[1]


def add_referral(user_id):
    cursor.execute(
        "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()


def set_vip(user_id, level):
    cursor.execute("UPDATE users SET vip=? WHERE user_id=?", (level, user_id))
    conn.commit()


def create_withdraw(user_id, amount):
    cursor.execute(
        "INSERT INTO withdrawals (user_id, amount) VALUES (?, ?)",
        (user_id, amount)
    )
    conn.commit()


def get_pending_withdraws():
    cursor.execute("SELECT * FROM withdrawals WHERE status='pending'")
    return cursor.fetchall()


def update_withdraw(id, status):
    cursor.execute("UPDATE withdrawals SET status=? WHERE id=?", (status, id))
    conn.commit()
