import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *
from economy import *
from admin import handle_admin_command

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

STATE = {}
ANTI_SPAM = {}

# ================= MENU =================
def menu(u, uid):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("💰 Wallet", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Marketplace", callback_data="market"),
        InlineKeyboardButton("📢 Ads", callback_data="ads")
    )

    kb.add(
        InlineKeyboardButton("➕ Add Task", callback_data="add_task"),
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
    )

    kb.add(
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer"),
        InlineKeyboardButton("👥 Referral", callback_data="ref")
    )

    if uid in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 Admin Panel", callback_data="admin"))

    return kb


def back():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back"))
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    u = get_user(m.from_user.id, m.from_user.username)
    await m.answer("🚀 SaaS Platform Ready", reply_markup=menu(u, m.from_user.id))


# ================= ADMIN COMMANDS =================
@dp.message_handler(lambda m: m.text.startswith("/"))
async def admin_cmd(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return

    res = handle_admin_command(m)
    if res:
        await m.answer(res)


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Balance: {u[2]}",
            reply_markup=back()
        )

    if c.data == "market":
        tasks = get_tasks()
        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 Join", callback_data=f"do_{t[0]}"))

            await c.message.answer(f"{t[2]}\n💰 {t[4]}", reply_markup=kb)

    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        if is_done(uid, tid):
            return await c.message.answer("❌ Done")

        t = next(x for x in get_tasks() if x[0] == tid)
        mark_done(uid, tid)
        add_points(uid, t[4])

        return await c.message.answer(f"+{t[4]} points")

    if c.data == "ads":
        ads = get_ads()
        for a in ads:
            await c.message.answer(f"📢 {a[2]}")

    if c.data == "withdraw":
        STATE[uid] = "withdraw"
        return await c.message.answer("Send: method address")

    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("Send: @user amount")

    if c.data == "add_task":
        STATE[uid] = "add_task"
        return await c.message.answer("Title | Link | Reward | Budget")

    if c.data == "admin":
        return await c.message.answer("🛠 Admin system active")


# ================= TEXT HANDLER =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)

    if uid not in STATE:
        return

    try:

        # WITHDRAW
        if STATE[uid] == "withdraw":
            method, address = m.text.split(" ", 1)
            STATE.pop(uid)
            return await m.answer("✅ Withdraw sent")

        # TRANSFER
        if STATE[uid] == "transfer":
            username, amount = m.text.split()
            amount = int(amount)

            cur.execute("SELECT * FROM users WHERE username=?", (username.replace("@",""),))
            target = cur.fetchone()

            if not target:
                return await m.answer("❌ User not found")

            transfer_points(uid, target[0], amount)

            STATE.pop(uid)
            return await m.answer("✅ Transfer done")

        # ADD TASK
        if STATE[uid] == "add_task":
            title, link, reward, budget = m.text.split("|")

            cur.execute("""
                INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)
            """, (uid, title, link, int(reward), int(budget), int(budget)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Task added")

    except:
        await m.answer("❌ Format error")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
