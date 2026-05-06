import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# ===== MENU =====
def menu(u):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💰 Wallet", callback_data="wallet"),
        InlineKeyboardButton("🧩 Marketplace", callback_data="tasks")
    )
    kb.add(
        InlineKeyboardButton("📢 Ads", callback_data="ads"),
        InlineKeyboardButton("👥 Referrals", callback_data="ref")
    )
    return kb

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    u = get_user(m.from_user.id, m.from_user.username)

    await m.answer("🚀 Welcome to Growth Platform", reply_markup=menu(u))

# ===== CALLBACK =====
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    # WALLET
    if c.data == "wallet":
        return await c.message.answer(f"💰 {u[2]} points")

    # TASK MARKET
    if c.data == "tasks":
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

    # TASK EXECUTE (growth loop)
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        use_task(tid)
        add_points(uid, 1)

        return await c.message.answer("🎉 +1 point")

    # REF SYSTEM
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"

        return await c.message.answer(
            f"👥 Invite & earn\n{link}"
        )

# ===== RUN =====
executor.start_polling(dp, skip_updates=True)
