import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *
from database import cur, conn  # مهم

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

RATE = 0.013
MIN_WITHDRAW = 100
BONUS = 10

STATE = {}
ANTI_SPAM = {}

# ================= UI =================
def menu(u):
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

    # ✅ FIXED ADMIN CHECK (safe type)
    if str(u[0]) in list(map(str, ADMIN_IDS)):
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
    await m.answer("🚀 SaaS Bot Ready", reply_markup=menu(u))


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    await c.answer()

    # ANTI SPAM
    now = time.time()
    if uid in ANTI_SPAM and now - ANTI_SPAM[uid] < 2:
        return
    ANTI_SPAM[uid] = now

    # BACK
    if c.data == "back":
        return await c.message.answer("🏠 Menu", reply_markup=menu(u))

    # WALLET
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[2]}\n💵 Value: {u[2]*RATE:.2f}$",
            reply_markup=back()
        )

    # BONUS
    if c.data == "bonus":
        if int(time.time()) - u[3] < 86400:
            return await c.message.answer("⏳ 24h cooldown")

        add_points(uid, BONUS)
        set_bonus(uid)
        return await c.message.answer("🎁 Bonus added")

    # MARKET
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

    # ADS
    if c.data == "ads":
        ads = get_ads()

        if not ads:
            return await c.message.answer("📢 No ads")

        for a in ads:
            await c.message.answer(f"📢 {a[2]}\n⏱ {a[3]}h")

    # ADD TASK
    if c.data == "add_task":
        STATE[uid] = "add_task"
        return await c.message.answer(
            "✍ Send task:\nTitle | Link | Reward | Budget"
        )

    # WITHDRAW
    if c.data == "withdraw":
        STATE[uid] = "withdraw"
        return await c.message.answer(f"💸 Min {MIN_WITHDRAW}\nSend: method address")

    # TRANSFER
    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("🔁 Send: @username amount")

    # REF
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        return await c.message.answer(f"👥 {link}")

    # ADMIN
    if c.data == "admin":
        ws = get_withdraws()

        if not ws:
            return await c.message.answer("❌ No withdraw requests")

        for w in ws:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ Approve", callback_data=f"ok_{w[0]}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"no_{w[0]}")
            )

            await c.message.answer(
                f"💸 User: {w[1]}\n💰 {w[2]}$\n📤 {w[3]} | {w[4]}",
                reply_markup=kb
            )

    # APPROVE / REJECT
    if c.data.startswith("ok_"):
        wid = int(c.data.split("_")[1])
        update_withdraw(wid, "approved")
        await c.message.answer("✅ Approved")

    if c.data.startswith("no_"):
        wid = int(c.data.split("_")[1])
        update_withdraw(wid, "rejected")
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

            cur.execute(
                "INSERT INTO withdraws (user_id,amount,method,address) VALUES (?,?,?,?)",
                (uid, u[2]*RATE, method, address)
            )
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Withdraw sent")

        # TRANSFER
        if STATE[uid] == "transfer":
            username, amount = m.text.split()
            amount = int(amount)

            username = username.replace("@", "")

            cur.execute("SELECT * FROM users WHERE username=?", (username,))
            target = cur.fetchone()

            if not target:
                return await m.answer("❌ User not found")

            target_id = target[0]

            if u[2] < amount:
                return await m.answer("❌ Not enough points")

            add_points(uid, -amount)
            add_points(target_id, amount)

            STATE.pop(uid)
            return await m.answer("✅ Transfer done")

        # ADD TASK
        if STATE[uid] == "add_task":
            title, link, reward, budget = m.text.split("|")

            reward = int(reward)
            budget = int(budget)

            if u[2] < 20:
                return await m.answer("❌ Need 20 points to post task")

            add_points(uid, -20)

            cur.execute("""
                INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)
            """, (uid, title, link, reward, budget, budget))
            conn.commit()

            STATE.pop(uid)

            return await m.answer("✅ Task published")

    except:
        await m.answer("❌ Wrong format")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
