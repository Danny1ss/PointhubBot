from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import BOT_TOKEN

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.answer("🔥 Pointhub Bot is running!")

executor.start_polling(dp, skip_updates=True)
