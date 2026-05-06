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


# ================= START FIX =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)

    # 🔥 IMPORTANT FIX: always init user
    if uid not in USER_TUTORIAL:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🚀 Start Guide", callback_data="guide_start"),
            InlineKeyboardButton("⏭ Skip", callback_data="guide_skip")
        )

        return await m.answer(
            "👋 Welcome to Reward Bot\n\n"
            "Earn points, ads, tasks, withdraw system.",
            reply_markup=kb
        )

    return await m.answer("🚀 Bot Ready", reply_markup=menu(u, uid))


# ================= CALLBACK (FIXED ORDER) =================
@dp.callback_query_handler(lambda c: True)
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    # ================= GUIDE SYSTEM MUST BE FIRST =================
    if c.data == "guide_skip":
        USER_TUTORIAL[uid] = True
        return await c.message.answer("✅ Guide skipped", reply_markup=menu(u, uid))

    if c.data == "guide_start":
        return await c.message.answer(
            "💰 STEP 1: Earn points from tasks\n\n"
            "🧩 STEP 2: Marketplace\n\n"
            "📢 STEP 3: Ads system\n\n"
            "💸 STEP 4: Withdraw system",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Finish ✅", callback_data="guide_finish")
            )
        )

    if c.data == "guide_finish":
        USER_TUTORIAL[uid] = True
        return await c.message.answer("🎉 You're ready!", reply_markup=menu(u, uid))

    # ================= SPAM =================
    now = time.time()
    if uid in ANTI_SPAM and now - ANTI_SPAM[uid] < 1.5:
        return
    ANTI_SPAM[uid] = now

    # ================= WALLET =================
    if c.data == "wallet":
        points = u[2] if u else 0
        return await c.message.answer(f"💰 Points: {points}\n💵 Value: {points * RATE:.2f}$")

    # ================= BONUS =================
    if c.data == "bonus":
        last = u[3] if u and len(u) > 3 else 0

        if time.time() - last < 86400:
            return await c.message.answer("⏳ Wait 24h")

        add_points(uid, BONUS_AMOUNT)
        set_bonus(uid)

        return await c.message.answer("🎁 Bonus added")

    # ================= BACKUP MENU =================
    if c.data == "back":
        return await c.message.answer("🏠 Menu", reply_markup=menu(u, uid))


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id

    if uid not in STATE:
        return

    if STATE[uid] == "task":
        title, link, reward, budget = m.text.split("|")

        cur.execute("INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)",
                    (uid, title, link, int(reward), int(budget), int(budget)))
        conn.commit()

        STATE.pop(uid)
        return await m.answer("✅ Task created")

    if STATE[uid] == "ad_text":
        STATE[uid] = {"text": m.text}

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("6h", callback_data="ad_6"),
            InlineKeyboardButton("12h", callback_data="ad_12")
        )
        kb.add(
            InlineKeyboardButton("24h", callback_data="ad_24"),
            InlineKeyboardButton("48h", callback_data="ad_48")
        )

        return await m.answer("⏳ Choose duration")


executor.start_polling(dp, skip_updates=True)
