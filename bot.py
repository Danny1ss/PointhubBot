import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from config import *
from database import *

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN missing")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ======================
# KEYBOARD
# ======================
menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add("💰 نقاطي", "🎁 مكافأة يومية")
menu.add("👑 VIP", "🔗 دعوة")
menu.add("💸 سحب أرباح")

admin_menu = ReplyKeyboardMarkup(resize_keyboard=True)
admin_menu.add("📊 احصائيات", "💎 اعطاء VIP")

# ======================
# START
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👋 أهلاً {message.from_user.first_name}\n"
        f"💰 نقاطك: {user[1]}",
        reply_markup=menu
    )

# ======================
# POINTS
# ======================
@dp.message_handler(lambda m: m.text == "💰 نقاطي")
async def points(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"💰 نقاطك: {user[1]}\n"
        f"👑 VIP: {VIP_LEVELS[user[2]]['name']}"
    )

# ======================
# DAILY BONUS
# ======================
@dp.message_handler(lambda m: m.text == "🎁 مكافأة يومية")
async def daily(message: types.Message):
    user = get_user(message.from_user.id)
    today = str(datetime.today().date())

    if user[4] == today:
        return await message.answer("❌ استلمت النهارده بالفعل")

    bonus = DAILY_BONUS * VIP_LEVELS[user[2]]["bonus"]

    add_points(message.from_user.id, int(bonus))
    set_daily(message.from_user.id, today)

    await message.answer(f"🎁 تم إضافة {int(bonus)} نقطة")

# ======================
# REFERRAL
# ======================
@dp.message_handler(lambda m: m.text == "🔗 دعوة")
async def ref(message: types.Message):
    link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"

    await message.answer(f"🔗 رابطك:\n{link}")

# ======================
# VIP
# ======================
@dp.message_handler(lambda m: m.text == "👑 VIP")
async def vip(message: types.Message):
    await message.answer(
        "👑 VIP Levels:\n"
        "VIP1 = x1.2\nVIP2 = x1.5\nVIP3 = x2"
    )

# ======================
# WITHDRAW
# ======================
@dp.message_handler(lambda m: m.text == "💸 سحب أرباح")
async def withdraw(message: types.Message):
    user = get_user(message.from_user.id)

    if user[1] < 50:
        return await message.answer("❌ الحد الأدنى للسحب 50 نقطة")

    create_withdraw(message.from_user.id, 50)
    add_points(message.from_user.id, -50)

    await message.answer("✅ تم إرسال طلب السحب")

# ======================
# ADMIN
# ======================
@dp.message_handler(lambda m: m.from_user.id in ADMIN_IDS and m.text == "📊 احصائيات")
async def stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]

    await message.answer(f"👥 المستخدمين: {count}")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
