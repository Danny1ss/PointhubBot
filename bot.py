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

# ================= UI =================
def menu(user):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({user[1]})", callback_data="acc"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Tasks", callback_data="tasks"),
        InlineKeyboardButton("➕ Add Task", callback_data="add_task")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw (100+)", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💸 Withdraws", callback_data="admin_w"),
        InlineKeyboardButton("🧩 Tasks", callback_data="admin_t")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("🚀 Welcome", reply_markup=menu(user))


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()  # 🔥 مهم جدًا (حل مشكلة loading)

    u = get_user(c.from_user.id)

    # ===== WALLET =====
    if c.data == "acc":
        return await c.message.answer(
            f"💰 Points: {u[1]}\n"
            f"👥 Ref: {u[2]}\n"
            f"💵 Value: {u[1]*0.013:.2f}$"
        )

    # ===== BONUS =====
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus available every 24h")

        add_points(c.from_user.id, 10)
        set_bonus(c.from_user.id)

        return await c.message.answer("🎁 Bonus added")

    # ===== TASKS =====
    elif c.data == "tasks":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks yet")

        msg = "🧩 Available Tasks:\n\n"
        for t in tasks:
            msg += f"🔗 Task: {t[2]}\n💰 Reward: {t[3]} pts\n\n"

        return await c.message.answer(msg)

    # ===== ADD TASK =====
    elif c.data == "add_task":
        state[c.from_user.id] = "task"
        return await c.message.answer(
            "➕ Send your task:\n"
            "🔗 link | 💰 reward"
        )

    # ===== WITHDRAW =====
    elif c.data == "withdraw":
        return await c.message.answer(
            "💸 Withdraw System\n\n"
            "Minimum: 100 points\n"
            "Format:\n"
            "method address\n\n"
            "Example:\n"
            "Vodafone 0100000000"
        )

    # ===== ADMIN =====
    if c.from_user.id in ADMIN_IDS:

        if c.data == "admin_w":
            w = get_withdraws()

            if not w:
                return await c.message.answer("❌ No requests")

            for i in w:
                await c.message.answer(
                    f"💸 ID: {i[0]}\n"
                    f"Amount: {i[2]}$\n"
                    f"Method: {i[3]}\n"
                    f"Address: {i[4] if len(i)>4 else 'N/A'}"
                )


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ===== ANTI SPAM =====
    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 2:
        return
    cooldown[uid] = now

    # ===== TASK FLOW =====
    if uid in state and state[uid] == "task":
        try:
            link, reward = m.text.split("|")
            add_task(uid, link.strip(), int(reward))
            state.pop(uid)
            return await m.answer("✅ Task added successfully")
        except:
            return await m.answer("❌ Correct format:\nlink | reward")

    # ===== WITHDRAW FIX (ONLY IF NOT TASK MODE) =====
    if uid not in state:
        if " " in m.text:
            method, address = m.text.split(" ", 1)

            if u[1] < 100:
                return await m.answer(
                    f"❌ Minimum withdrawal is 100 points\n"
                    f"💰 Your balance: {u[1]}"
                )

            amount = u[1] * 0.013

            create_withdraw(uid, amount, method, address)

            return await m.answer("✅ Withdrawal request sent")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
