import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}

# ================= SETTINGS =================
BONUS = 10
MIN_WITHDRAW = 100
RATE = 0.013
TASK_COST = 20

# ================= HELPERS =================
def broadcast(text):
    cur.execute("SELECT user_id FROM users")
    users = cur.fetchall()

    for u in users:
        try:
            bot.send_message(u[0], text)
        except:
            pass


# ================= UI =================
def main_menu(u):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("💰 Wallet", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Marketplace", callback_data="market"),
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")
    )

    kb.add(
        InlineKeyboardButton("👥 Referrals", callback_data="ref")
    )

    return kb


def market_menu():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("📢 Sell Offer", callback_data="sell"),
        InlineKeyboardButton("📣 Ads", callback_data="ads")
    )

    kb.add(
        InlineKeyboardButton("🎁 Gifts", callback_data="gift")
    )

    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel Active")

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

        return await c.message.answer(f"🎁 +{BONUS} points added")

    # ================= MARKET =================
    elif c.data == "market":
        return await c.message.answer("🧩 Marketplace", reply_markup=market_menu())

    # ================= SELL OFFER =================
    elif c.data == "sell":
        state[c.from_user.id] = "sell"
        return await c.message.answer(
            "🛒 Create Offer\n\nSend:\nTitle | Price | Description\n\n💡 Will be published in marketplace"
        )

    # ================= ADS =================
    elif c.data == "ads":
        state[c.from_user.id] = "ads"
        return await c.message.answer(
            "📢 Create Ad\n\nSend:\nText | Target Link\n\n💰 Cost: 20 points"
        )

    # ================= GIFTS =================
    elif c.data == "gift":
        state[c.from_user.id] = "gift"
        return await c.message.answer(
            "🎁 Gift Offer\nSend:\nGift Name | Price"
        )

    # ================= WITHDRAW =================
    elif c.data == "withdraw":
        state[c.from_user.id] = "withdraw"
        return await c.message.answer(
            "💸 Withdraw System\n\nSend:\nmethod address\n\nMin: 100 points"
        )

    # ================= REF =================
    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"

        return await c.message.answer(
            "👥 Referral System\n\n"
            f"🔗 Your link:\n{link}\n\n"
            "💰 Earn +10 per user"
        )


# ================= TEXT FLOW =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ================= SELL =================
    if uid in state and state[uid] == "sell":
        try:
            title, price, desc = m.text.split("|")

            broadcast(
                f"🛒 NEW OFFER\n\n"
                f"👤 @{m.from_user.username}\n"
                f"📌 {title}\n"
                f"💰 {price}\n"
                f"📝 {desc}"
            )

            state.pop(uid)

            return await m.answer("✅ Offer published to marketplace")

        except:
            return await m.answer("❌ format: title | price | desc")

    # ================= ADS =================
    if uid in state and state[uid] == "ads":
        try:
            text, link = m.text.split("|")

            if u[1] < 20:
                return await m.answer("❌ Not enough points")

            add_points(uid, -20)

            broadcast(
                f"📢 ADVERTISEMENT\n\n{text}\n\n🔗 {link}"
            )

            state.pop(uid)

            return await m.answer("✅ Ad published")

        except:
            return await m.answer("❌ format: text | link")

    # ================= WITHDRAW =================
    if uid in state and state[uid] == "withdraw":
        try:
            method, address = m.text.split(" ", 1)

            if u[1] < MIN_WITHDRAW:
                return await m.answer("❌ Minimum 100 points")

            create_withdraw(uid, u[1]*RATE, method, address)

            state.pop(uid)

            return await m.answer("✅ Withdraw request sent")

        except:
            return await m.answer("❌ format: method address")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
