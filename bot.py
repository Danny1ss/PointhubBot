import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
user_state = {}
withdraw_data = {}

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
        InlineKeyboardButton("📢 إعلان", callback_data="ad")
    )
    return kb


# ================= WITHDRAW UI =================
def withdraw_menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📱 Vodafone Cash", callback_data="w_vodafone"),
    )
    kb.add(
        InlineKeyboardButton("💰 TON", callback_data="w_ton"),
        InlineKeyboardButton("₿ Binance", callback_data="w_binance"),
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel")

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
            f"💵 القيمة: {u[1]*0.013:.2f}$"
        )

    elif c.data == "bonus":
        now = int(time.time())
        if now - u[3] < BONUS_COOLDOWN:
            return await c.message.answer("⏳ انتظر 24 ساعة")

        add_points(c.from_user.id, START_BONUS)
        set_last_bonus(c.from_user.id)

        await c.message.answer(f"🎁 +{START_BONUS} نقاط")

    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
        await c.message.answer(
            f"🔗 رابطك:\n{link}\n"
            f"🎁 لكل إحالة +{REFERRAL_BONUS}"
        )

    elif c.data == "ad":
        await c.message.answer(
            f"📢 اكتب إعلانك\n"
            f"💰 التكلفة: {AD_COST}"
        )

    # ===== WITHDRAW FLOW =====
    elif c.data == "withdraw":
        await c.message.answer("💸 اختر طريقة السحب:", reply_markup=withdraw_menu())

    elif c.data.startswith("w_"):
        method = c.data.split("_")[1]
        user_state[c.from_user.id] = method

        await c.message.answer("📥 اكتب رقمك أو عنوان المحفظة:")

    # ===== ADMIN =====
    if c.from_user.id not in ADMIN_IDS:
        return

    if c.data == "admin_w":
        data = get_withdraws()
        for w in data:
            await c.message.answer(
                f"💸 ID:{w[0]} | {w[2]}$ | {w[3]}\n"
                f"/ok_{w[0]} /no_{w[0]}"
            )


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    u = get_user(m.from_user.id)

    uid = m.from_user.id

    # ===== ADS =====
    if len(m.text) > 5 and not m.text.startswith("/"):
        if u[1] >= AD_COST:
            add_points(uid, -AD_COST)
            create_ad(uid, m.text)
            return await m.answer("📢 تم إرسال الإعلان")

    # ===== WITHDRAW INPUT =====
    if uid in user_state:
        method = user_state[uid]
        address = m.text

        amount = round(u[1] * 0.013, 2)

        withdraw_data[uid] = {
            "method": method,
            "address": address,
            "amount": amount
        }

        kb = InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("✔ تأكيد", callback_data="confirm_w"),
            InlineKeyboardButton("❌ إلغاء", callback_data="cancel_w")
        )

        await m.answer(
            f"💸 تأكيد السحب:\n"
            f"📌 الطريقة: {method}\n"
            f"📌 البيانات: {address}\n"
            f"💰 المبلغ: {amount}$",
            reply_markup=kb
        )

        return


# ================= CONFIRM WITHDRAW =================
@dp.callback_query_handler(lambda c: c.data in ["confirm_w", "cancel_w"])
async def confirm(c: types.CallbackQuery):

    uid = c.from_user.id

    if c.data == "cancel_w":
        user_state.pop(uid, None)
        withdraw_data.pop(uid, None)
        return await c.message.answer("❌ تم الإلغاء")

    data = withdraw_data.get(uid)
    if not data:
        return await c.message.answer("❌ لا يوجد طلب")

    create_withdraw(uid, data["amount"], data["method"], data["address"])

    user_state.pop(uid, None)
    withdraw_data.pop(uid, None)

    await c.message.answer("✅ تم إرسال الطلب للإدارة")


# ================= RUN =================
executor.start_polling(dp)
