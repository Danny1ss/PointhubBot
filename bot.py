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


def back():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back"))
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)

    if uid not in USER_TUTORIAL:
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("🚀 Start Guide", callback_data="guide_start"),
            InlineKeyboardButton("⏭ Skip", callback_data="guide_skip")
        )

        return await m.answer(
            "👋 Welcome!\nEarn points, run ads, complete tasks.",
            reply_markup=kb
        )

    await m.answer("🚀 Bot Ready", reply_markup=menu(u, uid))


# ================= CALLBACK =================
@dp.callback_query_handler(lambda c: True)
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    # SPAM PROTECTION
    now = time.time()
    if uid in ANTI_SPAM and now - ANTI_SPAM[uid] < 1.5:
        return
    ANTI_SPAM[uid] = now

    # BACK
    if c.data == "back":
        return await c.message.answer("🏠 Menu", reply_markup=menu(u, uid))

    # WALLET
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[2]}\n💵 Value: {u[2] * RATE:.2f}$",
            reply_markup=back()
        )

    # BONUS
    if c.data == "bonus":
        if time.time() - u[3] < 86400:
            return await c.message.answer("⏳ Wait 24h")

        add_points(uid, BONUS_AMOUNT)
        set_bonus(uid)
        return await c.message.answer("🎁 Bonus added")

    # MARKETPLACE
    if c.data == "market":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 Complete", callback_data=f"do_{t[0]}"))

            await c.message.answer(
                f"🧩 {t[2]}\n💰 {t[4]} pts",
                reply_markup=kb
            )

    # DO TASK SAFE
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        if is_done(uid, tid):
            return await c.message.answer("❌ Already done")

        task = next((x for x in get_tasks() if x[0] == tid), None)
        if not task:
            return await c.message.answer("❌ Task not found")

        mark_done(uid, tid)
        add_points(uid, task[4])

        return await c.message.answer(f"🎉 +{task[4]} pts")

    # ADS
    if c.data == "ads":
        ads = get_ads()

        if not ads:
            return await c.message.answer("📢 No ads")

        for a in ads:
            await c.message.answer(f"📢 {a[2]}")

    # ADD TASK
    if c.data == "add_task":
        STATE[uid] = "task"
        return await c.message.answer("Send: Title | Link | Reward | Budget")

    # ADD AD
    if c.data == "add_ad":
        STATE[uid] = "ad_text"
        return await c.message.answer("✍ Send ad text")

    # AD DURATION
    if c.data.startswith("ad_"):
        hours = int(c.data.split("_")[1])
        data = STATE.get(uid)

        if not isinstance(data, dict) or "text" not in data:
            return await c.message.answer("❌ Restart ad process")

        price = AD_PRICES.get(hours)

        if u[2] < price:
            return await c.message.answer("❌ Not enough points")

        add_points(uid, -price)

        cur.execute("INSERT INTO ads VALUES (NULL,?,?,?)",
                    (uid, data["text"], hours))
        conn.commit()

        STATE.pop(uid, None)

        return await c.message.answer("📢 Ad published")

    # HELP
    if c.data == "help":
        return await c.message.answer(
            "📘 GUIDE:\n"
            "Wallet - balance\nMarketplace - tasks\nAds - ads system\nAdd Ad - publish ads"
        )

    # ================= ADMIN =================
    if c.data == "admin":
        if uid not in ADMIN_IDS:
            return await c.message.answer("❌ Not allowed")

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("➕ Add Points", callback_data="adm_add"),
            InlineKeyboardButton("➖ Remove Points", callback_data="adm_remove")
        )
        kb.add(
            InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
            InlineKeyboardButton("🎁 Giveaway", callback_data="adm_give")
        )
        kb.add(InlineKeyboardButton("📢 Broadcast", callback_data="adm_broadcast"))

        return await c.message.answer("🛠 Admin Panel", reply_markup=kb)


# ================= TEXT HANDLER =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id

    if uid not in STATE:
        return

    # TASK
    if STATE[uid] == "task":
        try:
            title, link, reward, budget = m.text.split("|")

            cur.execute("INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)",
                        (uid, title, link, int(reward), int(budget), int(budget)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Task created")

        except:
            return await m.answer("❌ Format: Title | Link | Reward | Budget")

    # AD TEXT
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

    # WITHDRAW (REAL SAVE)
    if STATE[uid] == "withdraw":
        method, address = m.text.split(" ", 1)

        cur.execute("INSERT INTO withdraws VALUES (NULL,?,?,?,?)",
                    (uid, method, address, "pending"))
        conn.commit()

        STATE.pop(uid)
        return await m.answer("💸 Withdraw request sent")

    # TRANSFER SAFE
    if STATE[uid] == "transfer":
        try:
            username, amount = m.text.split()
            amount = int(amount)

            target = get_user(username)

            if not target:
                return await m.answer("❌ User not found")

            if u[2] < amount:
                return await m.answer("❌ Not enough points")

            add_points(uid, -amount)
            add_points(target[0], amount)

            STATE.pop(uid)
            return await m.answer("✅ Transfer done")

        except:
            return await m.answer("❌ Format: @user amount")


executor.start_polling(dp, skip_updates=True)
