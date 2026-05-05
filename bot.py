import logging
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
menu.add(
    KeyboardButton("💰 حسابي"),
    KeyboardButton("👥 إحالة")
)
menu.add(
    KeyboardButton("🎁 مكافأة"),
    KeyboardButton("💸 سحب")
)

# ======================
# START
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    args = message.get_args()

    inviter = int(args) if args.isdigit() else None

    user = get_user(user_id)

    if inviter and inviter != user_id:
        add_points(inviter, REFERRAL_BONUS)
        add_referral(inviter)

    await message.answer(
        f"👋 أهلاً {message.from_user.first_name}\n"
        f"💰 نقاطك: {user[1]}\n"
        f"💵 = {round(user[1]*POINTS_TO_USD, 2)}$",
        reply_markup=menu
    )

# ======================
@dp.message_handler(lambda m: m.text == "💰 حسابي")
async def account(message: types.Message):
    u = get_user(message.from_user.id)

    await message.answer(
        f"💰 نقاطك: {u[1]}\n"
        f"👥 إحالاتك: {u[3]}\n"
        f"💵 رصيدك: {round(u[1]*POINTS_TO_USD, 2)}$"
    )

# ======================
@dp.message_handler(lambda m: m.text == "👥 إحالة")
async def ref(message: types.Message):
    link = f"https://t.me/{(await bot.get_me()).username}?start={message.from_user.id}"

    await message.answer(
        f"👥 رابط الإحالة:\n{link}\n\n🎁 مكافأة: {REFERRAL_BONUS} نقاط"
    )

# ======================
@dp.message_handler(lambda m: m.text == "🎁 مكافأة")
async def bonus(message: types.Message):
    add_points(message.from_user.id, START_BONUS)
    u = get_user(message.from_user.id)

    await message.answer(f"🎁 +{START_BONUS}\n💰 {u[1]}")

# ======================
@dp.message_handler(lambda m: m.text == "💸 سحب")
async def withdraw(message: types.Message):
    u = get_user(message.from_user.id)

    if u[1] < MIN_WITHDRAW_POINTS:
        return await message.answer("❌ أقل سحب 100 نقطة")

    amount = round(u[1] * POINTS_TO_USD, 2)
    create_withdraw(message.from_user.id, amount)

    await message.answer(f"✅ تم طلب سحب {amount}$")

# ======================
# ADMIN PANEL
# ======================
@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer(
        "🛠 Admin Panel:\n"
        "/users\n/withdraws\n/give"
    )

# USERS
@dp.message_handler(commands=["users"])
async def users(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    await message.answer("📊 النظام يعمل")

# WITHDRAWS
@dp.message_handler(commands=["withdraws"])
async def withdraws(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    data = get_pending_withdraws()
    await message.answer(f"📤 طلبات: {len(data)}")

# GIVE POINTS
@dp.message_handler(commands=["give"])
async def give(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    try:
        _, uid, pts = message.text.split()
        add_points(int(uid), int(pts))
        await message.answer("✅ تم الإضافة")
    except:
        await message.answer("❌ /give user_id points")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
