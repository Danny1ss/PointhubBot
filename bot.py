import os
import logging
from aiogram import Bot, Dispatcher, executor, types

# تشغيل اللوجات
logging.basicConfig(level=logging.INFO)

# جلب التوكن من Railway Variables
BOT_TOKEN = os.getenv("BOT_TOKEN")

# التأكد إن التوكن موجود
if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is missing! Add it in Railway Variables")

# إنشاء البوت
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


# أمر /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("👋 أهلاً بيك! البوت شغال دلوقتي.")


# أي رسالة
@dp.message_handler()
async def echo(message: types.Message):
    await message.answer(f"انت كتبت: {message.text}")


# تشغيل البوت
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
