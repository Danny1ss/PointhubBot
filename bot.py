import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}
cooldown = {}

# ================= SETTINGS =================
BONUS = 10
MIN_WITHDRAW = 100
RATE = 0.013
TASK_COST = 20

# ================= UI =================
def main_menu(u):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({u[1]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Tasks", callback_data="tasks"),
        InlineKeyboardButton("➕ Add Task", callback_data="add_task")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    kb.add(
        InlineKeyboardButton("👥 Referrals", callback_data="ref")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("💸 Withdraws", callback_data="admin_w")
    )
    kb.add(
        InlineKeyboardButton("🧩 Proofs", callback_data="admin_t"),
        InlineKeyboardButton("📢 Broadcast", callback_data="admin_bc")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("🚀 Welcome", reply_markup=main_menu(user))


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()

    u = get_user(c.from_user.id)

    # ================= WALLET =================
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[1]}\n"
            f"💵 Value: {u[1]*RATE:.2f}$"
        )

    # ================= BONUS =================
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus every 24h")

        add_points(c.from_user.id, BONUS)
        set_bonus(c.from_user.id)

        return await c.message.answer(f"🎁 +{BONUS} points")

    # ================= TASKS =================
    elif c.data == "tasks":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(
                    f"📥 Execute ({t[3]} pts)",
                    callback_data=f"do:{t[0]}"
                )
            )

            await c.message.answer(
                f"🧩 Task\n🔗 {t[2]}\n💰 {t[3]} pts",
                reply_markup=kb
            )

    # ================= ADD TASK =================
    elif c.data == "add_task":
        state[c.from_user.id] = "task"
        return await c.message.answer(
            "➕ Create Task\n\nSend:\nlink | reward"
        )

    # ================= WITHDRAW =================
    elif c.data == "withdraw":
        state[c.from_user.id] = "withdraw"
        return await c.message.answer(
            "💸 Withdraw System\n\n"
            "Send: method + address\n"
            f"Min: {MIN_WITHDRAW} points"
        )

    # ================= TRANSFER =================
    elif c.data == "transfer":
        state[c.from_user.id] = "transfer"
        return await c.message.answer(
            "🔁 Transfer Points\n\nSend:\nuser_id amount"
        )

    # ================= REFERRALS =================
    elif c.data == "ref":
        return await c.message.answer(
            f"👥 Invite users:\n"
            f"Earn +10 points per user\n\n"
            f"Your ID: {c.from_user.id}"
        )

    # ================= ADMIN =================
    if c.from_user.id in ADMIN_IDS:

        if c.data == "admin_stats":
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM tasks")
            tasks = cur.fetchone()[0]

            await c.message.answer(
                f"📊 Stats:\n👥 {users}\n🧩 {tasks}"
            )

        if c.data == "admin_w":
            w = get_withdraws()

            if not w:
                return await c.message.answer("❌ No withdraws")

            for i in w:
                await c.message.answer(
                    f"💸 ID:{i[0]} | {i[2]}$ | {i[3]} {i[4]}\n"
                    f"/ok_{i[0]} /no_{i[0]}"
                )


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 2:
        return
    cooldown[uid] = now

    # ================= TASK =================
    if uid in state and state[uid] == "task":
        try:
            link, reward = m.text.split("|")

            if u[1] < TASK_COST:
                return await m.answer("❌ Not enough points")

            add_points(uid, -TASK_COST)
            add_task(uid, link, int(reward))

            state.pop(uid)

            return await m.answer("✅ Task created")

        except:
            return await m.answer("❌ link | reward")

    # ================= WITHDRAW =================
    if uid in state and state[uid] == "withdraw":
        method, address = m.text.split(" ", 1)

        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ Not enough points")

        create_withdraw(uid, u[1]*RATE, method, address)

        state.pop(uid)

        return await m.answer("✅ Withdraw sent")

    # ================= TRANSFER =================
    if uid in state and state[uid] == "transfer":
        try:
            to_id, amount = m.text.split()
            amount = int(amount)

            if u[1] < amount:
                return await m.answer("❌ Not enough balance")

            add_points(uid, -amount)
            add_points(int(to_id), amount)

            state.pop(uid)

            return await m.answer("✅ Transfer done")

        except:
            return await m.answer("❌ format: user_id amount")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
