import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from database import get_user, update_points, add_transaction, set_vip, add_referral

# ======================
# CONFIG
# ======================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# ======================
# INIT
# ======================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


# ======================
# START
# ======================
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"👋 أهلاً {message.from_user.first_name}\n\n"
        f"💰 نقاطك: {user[1]}\n"
        f"⭐ VIP: {user[2]}\n"
        f"👥 إحالات: {user[3]}\n\n"
        f"📌 /tasks المهام\n"
        f"📌 /balance الرصيد\n"
        f"📌 /withdraw السحب"
    )


# ======================
# BALANCE
# ======================
@dp.message_handler(commands=["balance"])
async def balance(message: types.Message):
    user = get_user(message.from_user.id)

    await message.answer(
        f"💰 رصيدك:\n\n"
        f"Points: {user[1]}\n"
        f"VIP: {user[2]}\n"
        f"Referrals: {user[3]}"
    )


# ======================
# TASKS
# ======================
@dp.message_handler(commands=["tasks"])
async def tasks(message: types.Message):
    await message.answer(
        "📌 مهام يومية:\n\n"
        "1) استخدم /daily (+10 نقاط)\n"
        "2) شارك البوت (+5 نقاط)"
    )


@dp.message_handler(commands=["daily"])
async def daily(message: types.Message):
    update_points(message.from_user.id, 10)
    add_transaction(message.from_user.id, "daily", 10)

    await message.answer("✅ حصلت على 10 نقاط")


# ======================
# REFERRAL SYSTEM
# ======================
@dp.message_handler(commands=["ref"])
async def ref(message: types.Message):
    user_id = message.from_user.id

    link = f"https://t.me/YOUR_BOT_USERNAME?start={user_id}"

    await message.answer(
        f"🔗 رابط الإحالة الخاص بك:\n{link}\n\n"
        f"💰 تربح نقاط لكل شخص يدخل"
    )


@dp.message_handler(lambda msg: msg.text and msg.text.startswith("/start "))
async def referral_handler(message: types.Message):
    try:
        ref_id = int(message.text.split()[1])

        if ref_id != message.from_user.id:
            add_referral(ref_id)
            update_points(ref_id, 5)
            add_transaction(ref_id, "referral", 5)

    except:
        pass


# ======================
# WITHDRAW SYSTEM
# ======================
@dp.message_handler(commands=["withdraw"])
async def withdraw(message: types.Message):
    user = get_user(message.from_user.id)

    if user[1] < 100:
        return await message.answer("❌ الحد الأدنى للسحب 100 نقطة")

    await message.answer(
        "💸 طلب السحب تم استلامه\n"
        "سيتم مراجعته من الإدارة"
    )

    add_transaction(message.from_user.id, "withdraw_request", user[1])


# ======================
# ADMIN PANEL
# ======================
@dp.message_handler(commands=["admin"])
async def admin(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        "🛠 لوحة الأدمن:\n\n"
        "/addpoints id amount\n"
        "/setvip id level"
    )


@dp.message_handler(commands=["addpoints"])
async def addpoints(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, uid, amount = message.text.split()
    update_points(int(uid), int(amount))

    await message.answer("✅ تم إضافة النقاط")


@dp.message_handler(commands=["setvip"])
async def vip(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return

    _, uid, level = message.text.split()
    set_vip(int(uid), int(level))

    await message.answer("⭐ تم تحديث VIP")


# ======================
# RUN
# ======================
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
