import time
import random
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

state = {}

# ================= SETTINGS =================
RATE = 0.013
MIN_WITHDRAW = 100
BONUS = 10

AD_PRICES = {
    "hour": ("⏱ ساعة", 15),
    "day": ("📆 يوم", 50),
    "week": ("📅 أسبوع", 200)
}

# ================= FIX BUTTONS (IMPORTANT) =================
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)

# ================= MENU =================
def menu(user):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 محفظتي ({user[1]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 مكافأة", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 السوق", callback_data="market"),
        InlineKeyboardButton("📢 إعلان", callback_data="ads")
    )

    kb.add(
        InlineKeyboardButton("💸 سحب", callback_data="withdraw"),
        InlineKeyboardButton("🔁 تحويل", callback_data="transfer")
    )

    kb.add(
        InlineKeyboardButton("👥 إحالات", callback_data="ref")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton("📊 إحصائيات", callback_data="admin_stats"),
        InlineKeyboardButton("💸 السحوبات", callback_data="admin_w")
    )

    kb.add(
        InlineKeyboardButton("🎁 رابط مكافأة", callback_data="admin_bonus")
    )

    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    kb = menu(user)

    if m.from_user.id in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 الأدمن", callback_data="admin"))

    await m.answer("🚀 أهلاً بيك في منصة الربح", reply_markup=kb)


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()

    u = get_user(c.from_user.id)

    # ===== WALLET =====
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 نقاطك: {u[1]}\n💵 قيمتها: {u[1]*RATE:.2f}$"
        )

    # ===== BONUS =====
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ كل 24 ساعة فقط")

        add_points(c.from_user.id, BONUS)
        set_bonus(c.from_user.id)

        return await c.message.answer("🎁 تم إضافة 10 نقاط")

    # ===== MARKET =====
    elif c.data == "market":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ لا يوجد مهام")

        for t in tasks:
            await c.message.answer(
                f"🧩 {t[2]}\n💰 {t[3]} نقطة"
            )

    # ===== ADS =====
    elif c.data == "ads":
        kb = InlineKeyboardMarkup()

        for k, v in AD_PRICES.items():
            kb.add(
                InlineKeyboardButton(f"{v[0]} - {v[1]} نقطة", callback_data=f"ad_{k}")
            )

        return await c.message.answer("📢 اختر نوع الإعلان", reply_markup=kb)

    elif c.data.startswith("ad_"):
        state[c.from_user.id] = c.data
        return await c.message.answer("✍ اكتب: نص الإعلان | الرابط")

    # ===== WITHDRAW =====
    elif c.data == "withdraw":
        kb = InlineKeyboardMarkup()

        kb.add(
            InlineKeyboardButton("📱 فودافون", callback_data="w_voda"),
            InlineKeyboardButton("💳 Binance", callback_data="w_binance")
        )

        return await c.message.answer("💸 اختر طريقة السحب", reply_markup=kb)

    elif c.data.startswith("w_"):
        state[c.from_user.id] = c.data
        return await c.message.answer("📥 اكتب بيانات السحب")

    # ===== TRANSFER =====
    elif c.data == "transfer":
        state[c.from_user.id] = "transfer"
        return await c.message.answer("✍ اكتب: @username 50")

    # ===== REF =====
    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"

        return await c.message.answer(f"👥 رابطك:\n{link}")

    # ===== ADMIN =====
    elif c.data == "admin":
        return await c.message.answer("🛠 لوحة الأدمن", reply_markup=admin_menu())

    elif c.data == "admin_stats":
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]

        return await c.message.answer(f"👥 المستخدمين: {users}")

    elif c.data == "admin_w":
        w = get_withdraws()

        if not w:
            return await c.message.answer("❌ لا يوجد طلبات")

        for i in w:
            await c.message.answer(f"💸 {i[2]}$ | {i[3]}")

    elif c.data == "admin_bonus":
        code = str(random.randint(10000,99999))
        save_bonus(code)

        link = f"https://t.me/{(await bot.get_me()).username}?start=bonus_{code}"

        return await c.message.answer(f"🎁 {link}")


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ===== ADS =====
    if uid in state and state[uid].startswith("ad_"):
        typ = state[uid].split("_")[1]
        price = AD_PRICES[typ][1]

        try:
            text, link = m.text.split("|")
        except:
            return await m.answer("❌ لازم: نص | رابط")

        if u[1] < price:
            return await m.answer("❌ نقاطك مش كفاية")

        add_points(uid, -price)

        cur.execute("SELECT user_id FROM users")
        users = cur.fetchall()

        for us in users:
            try:
                await bot.send_message(us[0], f"📢 {text}\n🔗 {link}")
            except:
                pass

        state.pop(uid)
        return await m.answer("✅ تم نشر الإعلان")

    # ===== WITHDRAW =====
    if uid in state and state[uid].startswith("w_"):
        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ الحد الأدنى 100 نقطة")

        method = state[uid]
        create_withdraw(uid, u[1]*RATE, method, m.text)

        state.pop(uid)

        return await m.answer("✅ تم إرسال طلب السحب")

    # ===== TRANSFER =====
    if uid in state and state[uid] == "transfer":
        try:
            username, amount = m.text.split()
            amount = int(amount)

            target = get_user_by_username(username.replace("@",""))

            if not target:
                return await m.answer("❌ المستخدم غير موجود")

            if u[1] < amount:
                return await m.answer("❌ رصيدك مش كفاية")

            add_points(uid, -amount)
            add_points(target[0], amount)

            state.pop(uid)

            return await m.answer("✅ تم التحويل")

        except:
            return await m.answer("❌ الصيغة: @username 50")


# ================= RUN =================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
