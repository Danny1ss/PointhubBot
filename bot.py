import os
import logging
from aiogram import Bot, Dispatcher, executor, types

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")  # حط التوكن في Railway Variables
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # اكتب ايديك هنا في Railway

# ======================
# INIT
# ======================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ======================
# SIMPLE DATABASE (in-memory)
# ======================
users = {}  # user_id -> points


# ======================
# HELPERS
# ======================
def get_user(user_id: int):
    if user_id not in users:
        users[user_id] = {
            "points": 0,
            "vip": 0,
            "tasks_done": 0
        }
    return users[user_id]


# ======================
# START COMMAND
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👋 أهلاً {message.from_user.first_name}\n\n"
        f"💰 نقاطك: {user['points']}\n"
        f"⭐ VIP: {user['vip']}\n\n"
        f"📌 استخدم /tasks لعرض المهام\n"
        f"📌 استخدم /balance لرصيدك"
    )


# ======================
# BALANCE
# ======================
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"💰 رصيدك الحالي:\n\n"
        f"Points: {user['points']}\n"
        f"VIP Level: {user['vip']}"
    )


# ======================
# SIMPLE TASK SYSTEM
# ======================
@dp.message_handler(commands=["tasks"])
async def tasks(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        "📌 المهام اليومية:\n\n"
        "1) شارك البوت (+10 نقاط)\n"
        "2) ادخل كل يوم (+5 نقاط)\n\n"
        "اكتب /done لإتمام مهمة بسيطة"
    )


@dp.message_handler(commands=["done"])
async def done(message: types.Message):
    user = get_user(message.from_user.id)

    user["points"] += 10
    user["tasks_done"] += 1

    await message.answer(
        f"✅ تم تسجيل المهمة!\n"
        f"+10 نقاط\n\n"
        f"💰 رصيدك الآن: {user['points']}"
    )


# ======================
# ADMIN PANEL (basic)
# ======================
@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ مش مصرح لك")

    total_users = len(users)

    await message.answer(
        f"🛠 لوحة الأدمن\n\n"
        f"👥 عدد المستخدمين: {total_users}\n\n"
        f"أوامر:\n"
        f"/addpoints id amount"
    )


@dp.message_handler(commands=["addpoints"])
async def add_points(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    try:
        _, user_id, amount = message.text.split()
        user_id = int(user_id)
        amount = int(amount)

        user = get_user(user_id)
        user["points"] += amount

        await message.answer("✅ تم إضافة النقاط")

    except:
        await message.answer("❌ الاستخدام: /addpoints id amount")


# ======================
# RUN
# ======================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
