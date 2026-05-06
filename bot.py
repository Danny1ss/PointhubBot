import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

STATE = {}
ANTI_SPAM = {}
USER_TUTORIAL = {}

AD_PRICES = {6: 20, 12: 35, 24: 50, 48: 90}
BONUS_AMOUNT = 10
RATE = 0.013


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
        InlineKeyboardButton("📢 Add Ad", callback_data="add_ad")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    kb.add(InlineKeyboardButton("📘 Help", callback_data="help"))

    if uid in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 Admin Panel", callback_data="admin"))

    return kb


# ================= ADMIN MENU =================
def admin_panel():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("➕ Add Points", callback_data="adm_add"),
        InlineKeyboardButton("➖ Remove Points", callback_data="adm_remove")
    )

    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
        InlineKeyboardButton("🎁 Giveaway", callback_data="adm_give")
    )

    kb.add(
        InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast")
    )

    return kb


# ================= CALLBACK =================
@dp.callback_query_handler(lambda c: True)
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    # ================= ADMIN PANEL =================
    if c.data == "admin":
        if uid not in ADMIN_IDS:
            return await c.message.answer("❌ Not allowed")
        return await c.message.answer("🛠 Admin Panel", reply_markup=admin_panel())


    # ================= ADD POINTS =================
    if c.data == "adm_add":
        STATE[uid] = "add_points"
        return await c.message.answer("Send: user_id amount")

    if c.data == "adm_remove":
        STATE[uid] = "remove_points"
        return await c.message.answer("Send: user_id amount")


    # ================= STATS =================
    if c.data == "adm_stats":
        cur.execute("SELECT COUNT(*), SUM(points) FROM users")
        data = cur.fetchone()

        return await c.message.answer(
            f"📊 Users: {data[0]}\n💰 Total Points: {data[1]}"
        )


    # ================= GIVEAWAY =================
    if c.data == "adm_give":
        STATE[uid] = "giveaway"
        return await c.message.answer("Send: points amount to give to ALL users")


    # ================= BROADCAST =================
    if c.data == "adm_broadcast":
        STATE[uid] = "broadcast"
        return await c.message.answer("Send message to broadcast")


# ================= TEXT HANDLER =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id

    if uid not in STATE:
        return

    # ================= ADD POINTS =================
    if STATE[uid] == "add_points":
        try:
            target, amount = m.text.split()
            amount = int(amount)

            add_points(int(target), amount)

            STATE.pop(uid)
            return await m.answer("✅ Points added")

        except:
            return await m.answer("❌ Format: user_id amount")


    # ================= REMOVE POINTS =================
    if STATE[uid] == "remove_points":
        try:
            target, amount = m.text.split()
            amount = int(amount)

            add_points(int(target), -amount)

            STATE.pop(uid)
            return await m.answer("✅ Points removed")

        except:
            return await m.answer("❌ Format: user_id amount")


    # ================= GIVEAWAY =================
    if STATE[uid] == "giveaway":
        try:
            amount = int(m.text)

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            for u in users:
                add_points(u[0], amount)

            STATE.pop(uid)
            return await m.answer("🎁 Giveaway sent to all users")

        except:
            return await m.answer("❌ Send valid number")


    # ================= BROADCAST =================
    if STATE[uid] == "broadcast":
        text = m.text

        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        for u in users:
            try:
                await bot.send_message(u[0], f"📢 {text}")
            except:
                pass

        STATE.pop(uid)
        return await m.answer("📢 Broadcast sent")


executor.start_polling(dp, skip_updates=True)
