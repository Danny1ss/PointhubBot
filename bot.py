import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}
cooldown = {}

# ================= UI =================
def menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Wallet", "acc"),
        InlineKeyboardButton("🎁 Bonus", "bonus")
    )
    kb.add(
        InlineKeyboardButton("🧩 Tasks", "tasks"),
        InlineKeyboardButton("➕ Add Task", "add_task")
    )
    kb.add(
        InlineKeyboardButton("💸 Withdraw", "withdraw"),
        InlineKeyboardButton("🔁 Transfer", "transfer")
    )
    return kb


def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💸 Withdraws", "admin_w"),
        InlineKeyboardButton("🧩 Tasks", "admin_t")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("🚀 Welcome to Platform", reply_markup=menu())


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    u = get_user(c.from_user.id)

    # ===== WALLET =====
    if c.data == "acc":
        await c.message.answer(
            f"💰 Points: {u[1]}\n"
            f"👥 Ref: {u[2]}\n"
            f"👑 VIP: {u[4]}\n"
            f"💵 Value: {u[1]*0.013:.2f}$"
        )

    # ===== BONUS (ANTI SPAM) =====
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus every 24h")

        add_points(c.from_user.id, 10)
        set_bonus(c.from_user.id)

        await c.message.answer("🎁 Bonus added")

    # ===== TASKS =====
    elif c.data == "tasks":
        t = get_tasks()
        if not t:
            return await c.message.answer("❌ No tasks")

        msg = "🧩 Tasks:\n\n"
        for x in t:
            msg += f"🔗 {x[2]} | 💰 {x[3]}\n"

        await c.message.answer(msg)

    # ===== ADD TASK =====
    elif c.data == "add_task":
        state[c.from_user.id] = "task"
        await c.message.answer("✍ send:\nlink | reward")

    # ===== WITHDRAW =====
    elif c.data == "withdraw":
        await c.message.answer("💸 Enter method + address")

    # ===== ADMIN =====
    if c.from_user.id in ADMIN_IDS:

        if c.data == "admin_w":
            w = get_withdraws()
            for i in w:
                await c.message.answer(
                    f"💸 ID:{i[0]} | {i[2]}$ | {i[3]}\n"
                    f"/ok_{i[0]} /no_{i[0]}"
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

    # ===== TASK ADD =====
    if uid in state and state[uid] == "task":
        try:
            link, reward = m.text.split("|")
            add_task(uid, link, int(reward))
            state.pop(uid)
            return await m.answer("✅ Task added")
        except:
            return await m.answer("❌ format: link | reward")

    # ===== WITHDRAW =====
    if " " in m.text:
        method, address = m.text.split(" ", 1)

        if u[1] < 100:
            return await m.answer("❌ Min withdraw 100 points")

        amount = u[1] * 0.013

        create_withdraw(uid, amount, method, address)

        return await m.answer("✅ Withdraw sent")


# ================= RUN =================
executor.start_polling(dp)
