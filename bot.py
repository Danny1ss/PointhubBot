import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import *
from database import *

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

# ================= UI =================
def menu():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("💰 حسابي", callback_data="acc"),
        InlineKeyboardButton("🎁 مكافأة", callback_data="bonus")
    )
    kb.add(
        InlineKeyboardButton("👥 إحالة", callback_data="ref"),
        InlineKeyboardButton("💸 سحب", callback_data="withdraw")
    )
    kb.add(
        InlineKeyboardButton("📢 إعلان", callback_data="ad")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):

    # اشتراك إجباري
    try:
        member = await bot.get_chat_member(CHANNEL.replace("https://t.me/", "@"), m.from_user.id)
        if member.status not in ["member", "creator", "administrator"]:
            return await m.answer(f"اشترك أولاً:\n{CHANNEL}")
    except:
        pass

    get_user(m.from_user.id)
    await m.answer("👋 أهلاً بك في النظام", reply_markup=menu())


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    u = get_user(c.from_user.id)

    if c.data == "acc":
        await c.message.answer(f"💰 نقاطك: {u[1]}")

    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
        await c.message.answer(link)

    elif c.data == "bonus":
        now = int(time.time())
        if now - u[3] < BONUS_COOLDOWN:
            return await c.message.answer("⏳ انتظر 24 ساعة")

        add_points(c.from_user.id, START_BONUS)
        await c.message.answer("🎁 تمت الإضافة")

    elif c.data == "withdraw":
        await c.message.answer("اكتب: method + address")

    elif c.data == "ad":
        await c.message.answer("اكتب إعلانك (خصم نقاط تلقائي)")


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    u = get_user(m.from_user.id)

    # AD SYSTEM
    if len(m.text) > 5:
        if u[1] >= AD_COST:
            add_points(m.from_user.id, -AD_COST)
            create_ad(m.from_user.id, m.text)
            return await m.answer("📢 تم إرسال الإعلان")

    # WITHDRAW
    try:
        method, address = m.text.split(maxsplit=1)
    except:
        return

    if u[1] < MIN_WITHDRAW:
        return await m.answer("❌ الحد الأدنى 100")

    amount = round(u[1] * 0.013, 2)

    create_withdraw(m.from_user.id, amount, method, address)

    await m.answer("✅ تم إرسال طلب السحب")


# ================= ADMIN =================
@dp.message_handler(commands=["admin"])
async def admin(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return

    await m.answer("🛠 Admin:\n/withdraws\n/ads")


@dp.message_handler(commands=["withdraws"])
async def withdraws(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return

    data = get_pending_withdraws()

    for w in data:
        await m.answer(
            f"💸 ID:{w[0]} | {w[1]}$ | {w[3]}\n"
            f"🔘 /approve_{w[0]} /reject_{w[0]}"
        )


@dp.message_handler(commands=["ads"])
async def ads(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return

    data = get_ads()

    for a in data:
        await m.answer(
            f"📢 Ad ID:{a[0]}\n{a[2]}\n"
            f"🔘 /ad_ok_{a[0]} /ad_no_{a[0]}"
        )


# ================= ADMIN ACTIONS =================
@dp.message_handler(lambda m: m.text.startswith("/approve_"))
async def approve_w(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    wid = int(m.text.split("_")[1])
    update_withdraw(wid, "approved")
    await m.answer("✅ Approved")


@dp.message_handler(lambda m: m.text.startswith("/reject_"))
async def reject_w(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    wid = int(m.text.split("_")[1])
    update_withdraw(wid, "rejected")
    await m.answer("❌ Rejected")


@dp.message_handler(lambda m: m.text.startswith("/ad_ok_"))
async def ad_ok(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    aid = int(m.text.split("_")[2])
    update_ad(aid, "approved")
    await m.answer("📢 Ad Approved")


@dp.message_handler(lambda m: m.text.startswith("/ad_no_"))
async def ad_no(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    aid = int(m.text.split("_")[2])
    update_ad(aid, "rejected")
    await m.answer("🚫 Ad Rejected")


# ================= RUN =================
executor.start_polling(dp)
