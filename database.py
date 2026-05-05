import sqlite3

conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

# ======================
# USERS TABLE
# ======================
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    points INTEGER DEFAULT 0,
    vip INTEGER DEFAULT 0,
    referrals INTEGER DEFAULT 0
)
""")

# ======================
# TRANSACTIONS TABLE
# ======================
cursor.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    type TEXT,
    amount INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()


# ======================
# USER FUNCTIONS
# ======================
def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    data = cursor.fetchone()

    if not data:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        return (user_id, 0, 0, 0)

    return data


def update_points(user_id, amount):
    cursor.execute(
        "UPDATE users SET points = points + ? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()


def add_transaction(user_id, type_, amount):
    cursor.execute(
        "INSERT INTO transactions (user_id, type, amount) VALUES (?, ?, ?)",
        (user_id, type_, amount)
    )
    conn.commit()


def set_vip(user_id, level):
    cursor.execute(
        "UPDATE users SET vip=? WHERE user_id=?",
        (level, user_id)
    )
    conn.commit()


def add_referral(user_id):
    cursor.execute(
        "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
        (user_id,)
    )
    conn.commit()
