import time
import random
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

STATE = {}
ANTI_SPAM = {}
USER_TUTORIAL = {}

# ================= ADS PRICES =================
AD_PRICES = {
    6: 20,
    12: 35,
    24: 50,
    48: 90
}

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

    kb.add(
        InlineKeyboardButton("📘 Help", callback_data="help")
    )

    if uid in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 Admin Panel", callback_data="admin"))

    return kb


def back():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Back", callback_data="back"))
    return kb


# ================= START + ONBOARDING =================
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
            "👋 Welcome to Reward Platform\n\n"
            "💡 Earn points, run ads, complete tasks and withdraw rewards.",
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
    if uid in ANTI_SPAM and now - ANTI_SPAM[uid] < 2:
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
                f"🧩 {t[2]}\n💰 Reward: {t[4]} pts",
                reply_markup=kb
            )

    # DO TASK
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        if is_done(uid, tid):
            return await c.message.answer("❌ Already done")

        t = next((x for x in get_tasks() if x[0] == tid), None)

        mark_done(uid, tid)
        add_points(uid, t[4])

        return await c.message.answer(f"🎉 +{t[4]} pts")

    # ADS LIST
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

    # ADD AD FLOW
    if c.data == "add_ad":
        STATE[uid] = "ad_text"
        return await c.message.answer("✍ Send ad text")

    # SELECT AD DURATION
    if c.data.startswith("ad_"):
        hours = int(c.data.split("_")[1])
        text = STATE.get(uid, {}).get("text")

        if not text:
            return await c.message.answer("❌ Restart ad process")

        price = AD_PRICES.get(hours)

        if u[2] < price:
            return await c.message.answer("❌ Not enough points")

        add_points(uid, -price)

        cur.execute("INSERT INTO ads VALUES (NULL,?,?,?)",
                    (uid, text, hours))
        conn.commit()

        STATE.pop(uid, None)

        return await c.message.answer("📢 Ad published")

    # HELP
    if c.data == "help":
        return await c.message.answer(
            "📘 GUIDE:\n\n"
            "💰 Wallet → balance\n"
            "🧩 Marketplace → tasks\n"
            "📢 Ads → view ads\n"
            "➕ Add Ad → publish ad\n\n"
            "💡 Earn by completing tasks and running ads"
        )

    # ADMIN PANEL
    if c.data == "admin":
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

        return await c.message.answer("🛠 Admin Panel", reply_markup=kb)

    # ================= GUIDE SYSTEM =================
    if c.data == "guide_skip":
        USER_TUTORIAL[uid] = True
        return await c.message.answer("✅ Guide skipped", reply_markup=menu(u, uid))

    if c.data == "guide_start":
        return await c.message.answer(
            "💰 STEP 1: Earn points from tasks\n"
            "🧩 STEP 2: Marketplace tasks\n"
            "📢 STEP 3: Ads system\n"
            "💸 STEP 4: Withdraw system",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("Finish ✅", callback_data="guide_finish")
            )
        )

    if c.data == "guide_finish":
        USER_TUTORIAL[uid] = True
        return await c.message.answer("🎉 You're ready!", reply_markup=menu(u, uid))


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id

    if uid not in STATE:
        return

    # TASK CREATE
    if STATE[uid] == "task":
        title, link, reward, budget = m.text.split("|")

        cur.execute("INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)",
                    (uid, title, link, int(reward), int(budget), int(budget)))
        conn.commit()

        STATE.pop(uid)
        return await m.answer("✅ Task created")

    # AD TEXT STEP
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

    # WITHDRAW
    if STATE[uid] == "withdraw":
        method, address = m.text.split(" ", 1)

        STATE.pop(uid)
        return await m.answer("✅ Withdraw sent")

    # TRANSFER
    if STATE[uid] == "transfer":
        username, amount = m.text.split()
        amount = int(amount)

        STATE.pop(uid)
        return await m.answer("✅ Transfer done")


executor.start_polling(dp, skip_updates=True)
