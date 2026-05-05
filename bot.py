import logging
import os
from aiogram import Bot, Dispatcher, types, executor

# ======================
# LOGGING
# ======================
logging.basicConfig(level=logging.INFO)

# ======================
# TOKEN (IMPORTANT)
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is missing in Railway Variables")

# ======================
# BOT INIT
# ======================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ======================
# START COMMAND
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer("✅ البوت شغال تمام")

# ======================
# TEST COMMAND
# ======================
@dp.message_handler(commands=["ping"])
async def ping(message: types.Message):
    await message.answer("🏓 pong")

# ======================
# RUN BOT
# ======================
if __name__ == "__main__":
    logging.info("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
