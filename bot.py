import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

RATE = 0.013
MIN_WITHDRAW = 100
AD_COST = 50
TASK_COST = 20
BONUS = 10

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
        InlineKeyboardButton("📢 Add Ad", callback_data="add_ad")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    kb.add(
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
    await m.answer("🚀 Bot Ready", reply_markup=menu(u, m.from_user.id))


# ================= CALLBACK =================
@dp.callback_query_handler(lambda c: True)
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

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
            f"💰 Points: {u[2]}",
            reply_markup=back()
        )

    # BONUS
    if c.data == "bonus":
        if int(time.time()) - u[3] < 86400:
            return await c.message.answer("⏳ Cooldown")

        add_points(uid, BONUS)
        set_bonus(uid)
        return await c.message.answer("🎁 Bonus added")

    # MARKETPLACE
    if c.data == "market":
        tasks = get_tasks()
        if not tasks:
            return await c.message.answer("❌ No tasks")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 Join", callback_data=f"do_{t[0]}"))
            await c.message.answer(f"{t[2]}\n💰 {t[4]}", reply_markup=kb)

    # DO TASK
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])

        if is_done(uid, tid):
            return await c.message.answer("❌ Already done")

        t = next((x for x in get_tasks() if x[0] == tid), None)
        if not t:
            return await c.message.answer("❌ Not found")

        mark_done(uid, tid)
        add_points(uid, t[4])

        return await c.message.answer(f"🎉 +{t[4]} pts")

    # ADS VIEW
    if c.data == "ads":
        ads = get_ads()
        if not ads:
            return await c.message.answer("❌ No ads")

        for a in ads:
            await c.message.answer(f"📢 {a[2]}")

    # ADD TASK
    if c.data == "add_task":
        STATE[uid] = "add_task"
        return await c.message.answer("✍ Title | Link | Reward | Budget")

    # ADD AD
    if c.data == "add_ad":
        STATE[uid] = "add_ad"
        return await c.message.answer(f"📢 Send: text | hours (Cost {AD_COST} pts)")

    # WITHDRAW
    if c.data == "withdraw":
        STATE[uid] = "withdraw"
        return await c.message.answer(f"💸 Min {MIN_WITHDRAW} Send: method address")

    # TRANSFER
    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("🔁 Send: @user amount")

    # REF
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        return await c.message.answer(f"👥 {link}")

    # ADMIN
    if c.data == "admin":
        ws = get_withdraws()
        if not ws:
            return await c.message.answer("❌ No withdraws")

        for w in ws:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Approve", callback_data=f"ok_{w[0]}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"no_{w[0]}")
            )
            await c.message.answer(f"{w[1]} | {w[2]}", reply_markup=kb)

    if c.data.startswith("ok_"):
        update_withdraw(int(c.data.split("_")[1]), "approved")
        await c.message.answer("✅ Approved")

    if c.data.startswith("no_"):
        update_withdraw(int(c.data.split("_")[1]), "rejected")
        await c.message.answer("❌ Rejected")


# ================= TEXT =================
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

            if u[2] < MIN_WITHDRAW:
                return await m.answer("❌ Not enough points")

            cur.execute("INSERT INTO withdraws VALUES (NULL,?,?,?,?)",
                        (uid, u[2]*RATE, method, address))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Sent")

        # TRANSFER
        if STATE[uid] == "transfer":
            username, amount = m.text.split()
            amount = int(amount)

            username = username.replace("@", "")

            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            target = cur.fetchone()

            if not target:
                return await m.answer("❌ Not found")

            if u[2] < amount:
                return await m.answer("❌ Not enough")

            add_points(uid, -amount)
            add_points(target[0], amount)

            STATE.pop(uid)
            return await m.answer("✅ Done")

        # ADD TASK
        if STATE[uid] == "add_task":
            title, link, reward, budget = m.text.split("|")

            if u[2] < TASK_COST:
                return await m.answer("❌ Need points")

            add_points(uid, -TASK_COST)

            cur.execute("INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)",
                        (uid, title, link, int(reward), int(budget), int(budget)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Task added")

        # ADD AD
        if STATE[uid] == "add_ad":
            text, hours = m.text.split("|")

            if u[2] < AD_COST:
                return await m.answer("❌ Not enough points")

            add_points(uid, -AD_COST)

            cur.execute("INSERT INTO ads VALUES (NULL,?,?,?)",
                        (uid, text, int(hours)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("📢 Ad published")

    except:
        await m.answer("❌ Format error")


executor.start_polling(dp, skip_updates=True)
