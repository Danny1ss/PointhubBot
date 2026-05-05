import logging
import os
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware

from config import BOT_TOKEN, START_BONUS
from database import get_user, update_points

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)

# ======================
# BOT INIT
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# ======================
# SAFE USER GET OR CREATE
# ======================
def ensure_user(user_id: int):
    try:
        return get_user(user_id)
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return None

# ======================
# START COMMAND
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    user = ensure_user(user_id)

    if not user:
        await message.answer("❌ حدث خطأ في إنشاء الحساب، حاول لاحقًا.")
        return

    await message.answer(
        f"👋 أهلاً {message.from_user.first_name}\n\n"
        f"🎯 تم تسجيلك بنجاح في النظام\n"
        f"💰 نقاطك: {user[1]}"
    )

# ======================
# POINTS COMMAND
# ======================
@dp.message_handler(commands=["points"])
async def points(message: types.Message):
    user = ensure_user(message.from_user.id)

    if not user:
        return await message.answer("❌ خطأ في جلب البيانات")

    await message.answer(f"💰 نقاطك الحالية: {user[1]}")

# ======================
# BONUS COMMAND (TEST)
# ======================
@dp.message_handler(commands=["bonus"])
async def bonus(message: types.Message):
    user_id = message.from_user.id

    update_points(user_id, START_BONUS)
    user = ensure_user(user_id)

    await message.answer(
        f"🎁 تم إضافة {START_BONUS} نقطة\n"
        f"💰 رصيدك الآن: {user[1]}"
    )

# ======================
# HELP COMMAND
# ======================
@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer(
        "📌 الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/points - عرض نقاطك\n"
        "/bonus - اختبار إضافة نقاط"
    )

# ======================
# FALLBACK (أي رسالة غير أوامر)
# ======================
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("🤖 استخدم /help لعرض الأوامر")

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    logging.info("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
