import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}
cooldown = {}

# ================= SETTINGS =================
BONUS = 10
MIN_WITHDRAW = 100
RATE = 0.013
TASK_COST = 20

# ================= UI =================
def main_menu(u):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({u[1]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Marketplace", callback_data="market"),
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
    )

    kb.add(
        InlineKeyboardButton("👥 Referrals", callback_data="ref"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("💸 Withdraws", callback_data="admin_w")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("🚀 Welcome to Earn Platform", reply_markup=main_menu(user))


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()

    u = get_user(c.from_user.id)

    # ================= WALLET =================
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[1]}\n"
            f"💵 Value: {u[1]*RATE:.2f}$"
        )

    # ================= BONUS =================
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus every 24h")

        add_points(c.from_user.id, BONUS)
        set_bonus(c.from_user.id)

        return await c.message.answer(f"🎁 +{BONUS} points")

    # ================= MARKETPLACE =================
    elif c.data == "market":

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📢 Channel Ads", callback_data="task_channel"),
            InlineKeyboardButton("🤖 Bot Ads", callback_data="task_bot")
        )
        kb.add(
            InlineKeyboardButton("🛒 Sell Offer", callback_data="task_sell"),
            InlineKeyboardButton("🎁 Gifts", callback_data="task_gift")
        )

        return await c.message.answer("🧩 Marketplace", reply_markup=kb)

    # ================= REFERRALS =================
    elif c.data == "ref":

        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"

        return await c.message.answer(
            "👥 Referral System\n\n"
            f"🔗 Your link:\n{link}\n\n"
            "💰 Earn +10 per user"
        )

    # ================= WITHDRAW =================
    elif c.data == "withdraw":

        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("📱 Vodafone Cash", callback_data="w_voda"),
            InlineKeyboardButton("💳 Binance", callback_data="w_binance")
        )
        kb.add(
            InlineKeyboardButton("💼 TON Wallet", callback_data="w_ton")
        )

        state[c.from_user.id] = "withdraw_step"

        return await c.message.answer(
            f"💸 Withdraw\nMin: {MIN_WITHDRAW}",
            reply_markup=kb
        )

    # ================= TRANSFER =================
    elif c.data == "transfer":
        state[c.from_user.id] = "transfer"
        return await c.message.answer("🔁 Send:\nuser_id amount")

    # ================= ADMIN =================
    if c.from_user.id in ADMIN_IDS:

        if c.data == "admin_stats":
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM tasks")
            tasks = cur.fetchone()[0]

            await c.message.answer(
                f"📊 Stats\n👥 Users: {users}\n🧩 Tasks: {tasks}"
            )


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 2:
        return
    cooldown[uid] = now

    # ================= WITHDRAW FLOW =================
    if uid in state and state[uid] == "withdraw_step":
        method = m.text

        state[uid] = "withdraw_address"
        state[f"{uid}_method"] = method

        return await m.answer("📤 Send your wallet/address")

    if uid in state and state[uid] == "withdraw_address":

        method = state.get(f"{uid}_method")
        address = m.text

        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ Not enough points")

        create_withdraw(uid, u[1]*RATE, method, address)

        state.pop(uid)
        state.pop(f"{uid}_method")

        return await m.answer("✅ Withdraw submitted")

    # ================= MARKETPLACE TASKS =================
    if uid in state and state[uid].startswith("task"):

        try:
            link, reward = m.text.split("|")

            if u[1] < TASK_COST:
                return await m.answer("❌ Not enough points")

            add_points(uid, -TASK_COST)
            add_task(uid, link, int(reward))

            state.pop(uid)

            return await m.answer("✅ Offer published")

        except:
            return await m.answer("❌ format: link | reward")

    # ================= TRANSFER =================
    if uid in state and state[uid] == "transfer":

        try:
            to_id, amount = m.text.split()
            amount = int(amount)

            if u[1] < amount:
                return await m.answer("❌ Not enough balance")

            add_points(uid, -amount)
            add_points(int(to_id), amount)

            state.pop(uid)

            return await m.answer("✅ Transferred")

        except:
            return await m.answer("❌ format: user_id amount")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
