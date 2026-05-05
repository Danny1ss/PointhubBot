import time
import random
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

state = {}

# ================= SETTINGS =================
RATE = 0.013
MIN_WITHDRAW = 100

AD_PRICES = {
    "hour": 15,
    "day": 50,
    "week": 200
}

# ================= MENU =================
def menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 Wallet", "wallet"),
        InlineKeyboardButton("🎁 Bonus", "bonus")
    )
    kb.add(
        InlineKeyboardButton("🧩 Tasks", "tasks"),
        InlineKeyboardButton("📢 Ads", "ads")
    )
    kb.add(
        InlineKeyboardButton("💸 Withdraw", "withdraw"),
        InlineKeyboardButton("🔁 Transfer", "transfer")
    )
    kb.add(
        InlineKeyboardButton("👥 Referral", "ref")
    )
    return kb

# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel")

    await m.answer("🚀 Welcome", reply_markup=menu())

# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()
    u = get_user(c.from_user.id)

    # ===== WALLET =====
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 {u[1]} points\n💵 {u[1]*RATE:.2f}$"
        )

    # ===== ADS MENU =====
    elif c.data == "ads":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("⏱ 1 Hour (15)", "ad_hour"),
            InlineKeyboardButton("📆 1 Day (50)", "ad_day"),
            InlineKeyboardButton("📅 1 Week (200)", "ad_week")
        )
        return await c.message.answer("📢 Choose Ad Type", reply_markup=kb)

    # ===== SELECT AD =====
    elif c.data.startswith("ad_"):
        typ = c.data.split("_")[1]
        state[c.from_user.id] = f"ad_{typ}"
        return await c.message.answer("✍ Send Ad Text + Link")

    # ===== TASKS =====
    elif c.data == "tasks":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks yet")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("✅ Done", f"done_{t[0]}"))

            await c.message.answer(
                f"🧩 {t[2]}\n💰 {t[3]} pts",
                reply_markup=kb
            )

    # ===== TRANSFER =====
    elif c.data == "transfer":
        state[c.from_user.id] = "transfer"
        return await c.message.answer("👤 Send @username + amount")

    # ===== WITHDRAW =====
    elif c.data == "withdraw":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("📱 Vodafone", "w_voda"),
            InlineKeyboardButton("💳 Binance", "w_binance")
        )
        return await c.message.answer("💸 Choose Method", reply_markup=kb)

    # ===== REF =====
    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"

        return await c.message.answer(
            f"👥 Invite & Earn\n{link}"
        )

# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ===== ADS SEND =====
    if uid in state and "ad_" in state[uid]:
        typ = state[uid].split("_")[1]
        price = AD_PRICES[typ]

        if u[1] < price:
            return await m.answer("❌ Not enough points")

        add_points(uid, -price)

        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        for us in users:
            try:
                await bot.send_message(us[0], f"📢 Ad:\n{m.text}")
            except:
                pass

        state.pop(uid)
        return await m.answer("✅ Ad Published")

    # ===== TRANSFER =====
    if uid in state and state[uid] == "transfer":
        try:
            username, amount = m.text.split()
            amount = int(amount)

            target = get_user_by_username(username.replace("@", ""))

            if not target:
                return await m.answer("❌ User not found")

            if u[1] < amount:
                return await m.answer("❌ Not enough points")

            add_points(uid, -amount)
            add_points(target[0], amount)

            state.pop(uid)

            return await m.answer("✅ Sent")

        except:
            return await m.answer("❌ @username amount")

# ================= RUN =================
executor.start_polling(dp)
