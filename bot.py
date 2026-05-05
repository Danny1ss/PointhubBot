from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
import os

bot = Bot(token=os.getenv("8611419165:AAHtnbEpdOP9o_sjSw4FZ9jfMgUnVxgwwkI"))
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🔥 Bot is running!")

executor.start_polling(dp, skip_updates=True)
