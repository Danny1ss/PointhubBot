import time
import random
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}

# ================= SETTINGS =================
RATE = 0.013
MIN_WITHDRAW = 100
BONUS = 10

AD_PRICES = {
    "hour": 15,
    "day": 50,
    "week": 200
}

# ================= UI =================
def main_menu(user):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({user[1]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Marketplace", callback_data="market"),
        InlineKeyboardButton("📢 Ads", callback_data="ads")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    kb.add(
        InlineKeyboardButton("👥 Referral", callback_data="ref")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
        InlineKeyboardButton("💸 Withdraws", callback_data="admin_w")
    )

    kb.add(
        InlineKeyboardButton("🎁 Bonus Link", callback_data="admin_bonus")
    )

    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    kb = main_menu(user)

    # إضافة زر الأدمن
    if m.from_user.id in ADMIN_IDS:
        kb.add(
            InlineKeyboardButton("🛠 Admin Panel", callback_data="admin_panel")
        )

    await m.answer("🚀 Welcome", reply_markup=kb)


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()

    u = get_user(c.from_user.id)

    # ===== WALLET =====
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[1]}\n💵 Value: {u[1]*RATE:.2f}$"
        )

    # ===== BONUS =====
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus every 24h")

        add_points(c.from_user.id, BONUS)
        set_bonus(c.from_user.id)

        return await c.message.answer(f"🎁 +{BONUS} points")

    # ===== MARKET =====
    elif c.data == "market":
        kb = InlineKeyboardMarkup(row_width=2)
        kb.add(
            InlineKeyboardButton("🛒 Sell Offer", "sell"),
            InlineKeyboardButton("🎁 Gifts", "gift")
        )
        return await c.message.answer("🧩 Marketplace", reply_markup=kb)

    # ===== SELL =====
    elif c.data == "sell":
        state[c.from_user.id] = "sell"
        return await c.message.answer("✍ Send:\nTitle | Price | Description")

    # ===== ADS =====
    elif c.data == "ads":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("⏱ 1 Hour (15)", "ad_hour"),
            InlineKeyboardButton("📆 1 Day (50)", "ad_day"),
            InlineKeyboardButton("📅 Week (200)", "ad_week")
        )
        return await c.message.answer("📢 Choose Ad", reply_markup=kb)

    elif c.data.startswith("ad_"):
        typ = c.data.split("_")[1]
        state[c.from_user.id] = f"ad_{typ}"
        return await c.message.answer("✍ Send Ad Text + Link")

    # ===== WITHDRAW =====
    elif c.data == "withdraw":
        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("📱 Vodafone Cash", "w_voda"),
            InlineKeyboardButton("💳 Binance", "w_binance")
        )
        kb.add(
            InlineKeyboardButton("💼 TON Wallet", "w_ton")
        )
        state[c.from_user.id] = "withdraw_method"
        return await c.message.answer("💸 Choose Method", reply_markup=kb)

    elif c.data.startswith("w_"):
        method = c.data.replace("w_", "")
        state[c.from_user.id] = f"withdraw_{method}"
        return await c.message.answer("📤 Send your number / address")

    # ===== TRANSFER =====
    elif c.data == "transfer":
        state[c.from_user.id] = "transfer"
        return await c.message.answer("👤 Send:\n@username amount")

    # ===== REF =====
    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
        return await c.message.answer(f"👥 Invite:\n{link}")

    # ===== ADMIN =====
    elif c.data == "admin_panel":
        return await c.message.answer("🛠 Admin Panel", reply_markup=admin_menu())

    elif c.data == "admin_stats":
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        return await c.message.answer(f"👥 Users: {users}")

    elif c.data == "admin_w":
        w = get_withdraws()

        if not w:
            return await c.message.answer("❌ No withdraws")

        for i in w:
            await c.message.answer(
                f"💸 {i[2]}$ | {i[3]}"
            )

    elif c.data == "admin_bonus":
        code = str(random.randint(10000,99999))
        save_bonus(code)

        link = f"https://t.me/{(await bot.get_me()).username}?start=bonus_{code}"

        return await c.message.answer(f"🎁 Link:\n{link}")


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ===== SELL =====
    if uid in state and state[uid] == "sell":
        try:
            title, price, desc = m.text.split("|")

            cur.execute("SELECT user_id FROM users")
            users = cur.fetchall()

            for us in users:
                try:
                    await bot.send_message(
                        us[0],
                        f"🛒 {title}\n💰 {price}\n📝 {desc}\n👤 @{m.from_user.username}"
                    )
                except:
                    pass

            state.pop(uid)
            return await m.answer("✅ Published")

        except:
            return await m.answer("❌ format: title | price | desc")

    # ===== ADS =====
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
        return await m.answer("✅ Ad sent")

    # ===== WITHDRAW =====
    if uid in state and state[uid].startswith("withdraw_"):
        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ Minimum 100 points")

        method = state[uid].replace("withdraw_", "")
        create_withdraw(uid, u[1]*RATE, method, m.text)

        state.pop(uid)

        return await m.answer("✅ Withdraw sent")

    # ===== TRANSFER =====
    if uid in state and state[uid] == "transfer":
        try:
            username, amount = m.text.split()
            amount = int(amount)

            target = get_user_by_username(username.replace("@",""))

            if not target:
                return await m.answer("❌ User not found")

            if u[1] < amount:
                return await m.answer("❌ Not enough points")

            add_points(uid, -amount)
            add_points(target[0], amount)

            state.pop(uid)

            return await m.answer("✅ Transfer done")

        except:
            return await m.answer("❌ @username amount")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
