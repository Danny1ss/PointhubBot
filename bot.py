import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)


# ================= UI =================
def menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💰 حسابي", callback_data="acc"),
        InlineKeyboardButton("🎁 بونص", callback_data="bonus")
    )
    kb.add(
        InlineKeyboardButton("👥 إحالة", callback_data="ref"),
        InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    kb.add(
        InlineKeyboardButton("📢 إعلان", callback_data="ad"),
    )
    return kb


def admin_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="admin_w"),
        InlineKeyboardButton("📢 Ads", callback_data="admin_a")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("👋 أهلاً بك", reply_markup=menu())


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    u = get_user(c.from_user.id)

    # ===== USER =====
    if c.data == "acc":
        await c.message.answer(
            f"💰 نقاطك: {u[1]}\n"
            f"👥 إحالاتك: {u[2]}\n"
            f"💵 قيمتها: {u[1]*0.013:.2f}$"
        )

    # 🔥 BONUS 24H SYSTEM
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < BONUS_COOLDOWN:
            remain = BONUS_COOLDOWN - (now - u[3])
            return await c.message.answer(f"⏳ انتظر {remain//3600} ساعة")

        add_points(c.from_user.id, START_BONUS)
        set_last_bonus(c.from_user.id)

        await c.message.answer(f"🎁 +{START_BONUS} نقاط")

    # 👥 REF
    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
        await c.message.answer(
            f"🔗 رابطك:\n{link}\n"
            f"🎁 تربح {REFERRAL_BONUS} نقاط لكل إحالة"
        )

    # 💸 WITHDRAW
    elif c.data == "withdraw":
        await c.message.answer("💸 اكتب: method address")

    # 📢 ADS
    elif c.data == "ad":
        await c.message.answer(
            f"📢 اكتب إعلانك\n"
            f"💰 التكلفة: {AD_COST} نقطة"
        )

    # ===== ADMIN =====
    if c.from_user.id not in ADMIN_IDS:
        return

    if c.data == "admin_w":
        from database import get_withdraws
        data = get_withdraws()
        for w in data:
            await c.message.answer(
                f"💸 ID:{w[0]} | {w[2]}$ | {w[3]}\n"
                f"/ok_{w[0]} /no_{w[0]}"
            )

    elif c.data == "admin_a":
        ads = get_ads()
        for a in ads:
            await c.message.answer(
                f"📢 {a[2]}\n"
                f"/adok_{a[0]} /adno_{a[0]}"
            )


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    u = get_user(m.from_user.id)

    # 📢 ADS
    if len(m.text) > 5 and not m.text.startswith("/"):
        if u[1] >= AD_COST:
            add_points(m.from_user.id, -AD_COST)
            create_ad(m.from_user.id, m.text)
            return await m.answer("📢 تم نشر الإعلان")

    # 💸 WITHDRAW FIX
    if " " in m.text:
        method, address = m.text.split(" ", 1)

        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ الحد الأدنى 100")

        amount = round(u[1] * 0.013, 2)

        create_withdraw(m.from_user.id, amount, method, address)

        await m.answer("✅ تم إرسال السحب")


# ================= RUN =================
executor.start_polling(dp)
