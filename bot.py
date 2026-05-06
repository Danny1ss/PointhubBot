import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

RATE = 0.013
MIN_WITHDRAW = 100
BONUS = 10

# ================= MENU =================
def menu(u):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({u[2]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Marketplace", callback_data="market"),
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
    )

    kb.add(
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer"),
        InlineKeyboardButton("👥 Referral", callback_data="ref")
    )

    if u[0] in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 Admin", callback_data="admin"))

    return kb

# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    u = get_user(m.from_user.id, m.from_user.username)

    await m.answer("🚀 Welcome", reply_markup=menu(u))

# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    # ===== WALLET =====
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[2]}\n💵 ${u[2]*RATE:.2f}"
        )

    # ===== BONUS =====
    if c.data == "bonus":
        if int(time.time()) - u[3] < 86400:
            return await c.message.answer("⏳ 24h cooldown")

        add_points(uid, BONUS)
        set_bonus(uid)

        return await c.message.answer(f"🎁 +{BONUS}")

    # ===== MARKET =====
    if c.data == "market":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 Join", callback_data=f"do_{t[0]}"))

            await c.message.answer(
                f"🧩 {t[2]}\n💰 {t[4]} pts",
                reply_markup=kb
            )

    # ===== DO TASK =====
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        if is_done(uid, tid):
            return await c.message.answer("❌ Already done")

        t = get_task(tid)

        mark_done(uid, tid)
        add_points(uid, t[4])

        return await c.message.answer(f"🎉 +{t[4]} points")

    # ===== WITHDRAW =====
    if c.data == "withdraw":
        return await c.message.answer(f"💸 Min withdraw {MIN_WITHDRAW}")

    # ===== TRANSFER =====
    if c.data == "transfer":
        return await c.message.answer("🔁 Send: @user amount")

    # ===== REF =====
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"

        return await c.message.answer(f"👥 {link}")

    # ===== ADMIN =====
    if c.data == "admin":
        return await c.message.answer("🛠 Admin Panel")

# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    await m.answer("ℹ️ Use buttons only")

# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
