from database import cur, conn

def add_points(user_id, amount):
    cur.execute("UPDATE users SET points = points + ? WHERE user_id=?", (amount, user_id))
    conn.commit()

def get_balance(user_id):
    cur.execute("SELECT points FROM users WHERE user_id=?", (user_id,))
    r = cur.fetchone()
    return r[0] if r else 0

def transfer_points(sender, receiver, amount):
    if get_balance(sender) < amount:
        return False

    add_points(sender, -amount)
    add_points(receiver, amount)
    return True
