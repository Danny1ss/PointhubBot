import logging
from aiogram import Bot, Dispatcher, types, executor

from config import BOT_TOKEN, START_BONUS
from database import get_user, update_points

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)

# ======================
# CHECK TOKEN
# ======================
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in Railway Variables")

# ======================
# BOT INIT
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ======================
# SAFE USER
# ======================
def ensure_user(user_id: int):
    try:
        return get_user(user_id)
    except Exception as e:
        logging.error(f"DB Error: {e}")
        return None

# ======================
# START
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = ensure_user(message.from_user.id)

    if not user:
        return await message.answer("❌ Error creating account")

    await message.answer(
        f"👋 Welcome {message.from_user.first_name}\n"
        f"💰 Points: {user[1]}"
    )

# ======================
# POINTS
# ======================
@dp.message_handler(commands=["points"])
async def points(message: types.Message):
    user = ensure_user(message.from_user.id)

    if not user:
        return await message.answer("❌ Error")

    await message.answer(f"💰 Points: {user[1]}")

# ======================
# BONUS
# ======================
@dp.message_handler(commands=["bonus"])
async def bonus(message: types.Message):
    user_id = message.from_user.id

    update_points(user_id, START_BONUS)
    user = ensure_user(user_id)

    if user:
        await message.answer(
            f"🎁 +{START_BONUS} points\n"
            f"💰 Total: {user[1]}"
        )

# ======================
# HELP
# ======================
@dp.message_handler(commands=["help"])
async def help_cmd(message: types.Message):
    await message.answer(
        "/start\n/points\n/bonus"
    )

# ======================
# FALLBACK
# ======================
@dp.message_handler()
async def fallback(message: types.Message):
    await message.answer("Use /help")

# ======================
# RUN
# ======================
if __name__ == "__main__":
    logging.info("Bot started")
    executor.start_polling(dp, skip_updates=True)
