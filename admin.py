from economy import add_points, get_balance
from database import cur, conn

def handle_admin_command(message):
    text = message.text
    parts = text.split()

    cmd = parts[0]

    # ➕ Add points
    if cmd == "/addpoints":
        user_id = int(parts[1])
        amount = int(parts[2])
        add_points(user_id, amount)
        return "✅ Points added"

    # ➖ Remove points
    if cmd == "/removepoints":
        user_id = int(parts[1])
        amount = int(parts[2])
        add_points(user_id, -amount)
        return "✅ Points removed"

    # 💰 Balance
    if cmd == "/balance":
        user_id = int(parts[1])
        return f"💰 Balance: {get_balance(user_id)}"

    # 📢 Broadcast
    if cmd == "/broadcast":
        msg = text.replace("/broadcast", "")
        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        for u in users:
            try:
                message.bot.send_message(u[0], msg)
            except:
                pass

        return "📢 Broadcast sent"

    # 📊 Stats
    if cmd == "/stats":
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks")
        tasks = cur.fetchone()[0]

        return f"""
📊 STATS:
👤 Users: {users}
🧩 Tasks: {tasks}
"""

    return None
