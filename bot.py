import time
import random
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

RATE = 0.013
MIN_WITHDRAW = 100
BONUS = 10
AD_COST = 50
TASK_COST = 20

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


# ================= ADMIN COMMANDS =================
@dp.message_handler(lambda m: m.from_user.id in ADMIN_IDS and m.text.startswith("/"))
async def admin_cmds(m: types.Message):
    try:
        args = m.text.split()

        # ➕ Add Points
        if args[0] == "/addpoints":
            add_points(int(args[1]), int(args[2]))
            return await m.answer("✅ Points added")

        # ➖ Remove Points
        if args[0] == "/removepoints":
            add_points(int(args[1]), -int(args[2]))
            return await m.answer("✅ Points removed")

        # 🎁 Giveaway
        if args[0] == "/giveaway":
            amount = int(args[1])

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            winner = random.choice(users)[0]
            add_points(winner, amount)

            return await m.answer(f"🎉 Winner: {winner}\n+{amount} pts")

        # 📢 Broadcast
        if args[0] == "/broadcast":
            msg = m.text.replace("/broadcast", "")

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            for u in users:
                try:
                    await bot.send_message(u[0], msg)
                except:
                    pass

            return await m.answer("📢 Sent")

        # 📊 Stats
        if args[0] == "/stats":
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM tasks")
            tasks = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM ads")
            ads = cur.fetchone()[0]

            return await m.answer(
                f"📊 STATS\n👤 Users: {users}\n🧩 Tasks: {tasks}\n📢 Ads: {ads}"
            )

    except:
        await m.answer("❌ Error")


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
        return await c.message.answer(f"💰 Points: {u[2]}", reply_markup=back())

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
        mark_done(uid, tid)
        add_points(uid, t[4])

        return await c.message.answer(f"🎉 +{t[4]} pts")

    # ADS
    if c.data == "ads":
        ads = get_ads()
        for a in ads:
            await c.message.answer(f"📢 {a[2]}")

    # ADD TASK
    if c.data == "add_task":
        STATE[uid] = "add_task"
        return await c.message.answer("Title | Link | Reward | Budget")

    # ADD AD
    if c.data == "add_ad":
        STATE[uid] = "add_ad"
        return await c.message.answer("Text | hours (cost 50 pts)")

    # WITHDRAW
    if c.data == "withdraw":
        STATE[uid] = "withdraw"
        return await c.message.answer("Send: method address")

    # TRANSFER
    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("Send: @user amount")

    # REF
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        return await c.message.answer(link)

    # ================= ADMIN PANEL =================
    if c.data == "admin":
        kb = InlineKeyboardMarkup(row_width=2)

        kb.add(
            InlineKeyboardButton("💸 Withdraws", callback_data="admin_w"),
            InlineKeyboardButton("🎁 Giveaway", callback_data="admin_g")
        )

        kb.add(
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_b"),
            InlineKeyboardButton("📊 Stats", callback_data="admin_s")
        )

        return await c.message.answer("🛠 Admin Panel", reply_markup=kb)

    # WITHDRAW LIST
    if c.data == "admin_w":
        ws = get_withdraws()
        for w in ws:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅", callback_data=f"ok_{w[0]}"),
                InlineKeyboardButton("❌", callback_data=f"no_{w[0]}")
            )
            await c.message.answer(f"{w[1]} | {w[2]}", reply_markup=kb)

    # GIVEAWAY
    if c.data == "admin_g":
        STATE[uid] = "giveaway"
        return await c.message.answer("🎁 Send amount")

    # BROADCAST
    if c.data == "admin_b":
        STATE[uid] = "broadcast"
        return await c.message.answer("📢 Send message")

    # STATS
    if c.data == "admin_s":
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM tasks")
        tasks = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM ads")
        ads = cur.fetchone()[0]

        return await c.message.answer(f"Users:{users}\nTasks:{tasks}\nAds:{ads}")

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

    if uid not in STATE:
        return

    try:

        # WITHDRAW
        if STATE[uid] == "withdraw":
            method, address = m.text.split(" ", 1)
            STATE.pop(uid)
            return await m.answer("✅ Sent")

        # TRANSFER
        if STATE[uid] == "transfer":
            username, amount = m.text.split()
            amount = int(amount)

            cur.execute("SELECT * FROM users WHERE username=?", (username.replace("@",""),))
            t = cur.fetchone()

            if not t:
                return await m.answer("❌ Not found")

            add_points(uid, -amount)
            add_points(t[0], amount)

            STATE.pop(uid)
            return await m.answer("✅ Done")

        # ADD TASK
        if STATE[uid] == "add_task":
            title, link, reward, budget = m.text.split("|")

            cur.execute("INSERT INTO tasks VALUES (NULL,?,?,?,?,?,?)",
                        (uid, title, link, int(reward), int(budget), int(budget)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("✅ Task added")

        # ADD AD
        if STATE[uid] == "add_ad":
            text, hours = m.text.split("|")

            add_points(uid, -AD_COST)

            cur.execute("INSERT INTO ads VALUES (NULL,?,?,?)",
                        (uid, text, int(hours)))
            conn.commit()

            STATE.pop(uid)
            return await m.answer("📢 Ad added")

        # GIVEAWAY EXECUTE
        if STATE[uid] == "giveaway":
            amount = int(m.text)

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            winner = random.choice(users)[0]
            add_points(winner, amount)

            STATE.pop(uid)
            return await m.answer(f"🎉 Winner: {winner}")

        # BROADCAST EXECUTE
        if STATE[uid] == "broadcast":
            msg = m.text

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            for u in users:
                try:
                    await bot.send_message(u[0], msg)
                except:
                    pass

            STATE.pop(uid)
            return await m.answer("📢 Sent")

    except:
        await m.answer("❌ Error format")


executor.start_polling(dp, skip_updates=True)
