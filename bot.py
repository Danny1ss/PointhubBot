import time
import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

logging.basicConfig(level=logging.INFO)

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN missing")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

STATE = {}

RATE = 0.013
MIN_WITHDRAW = 100
DAILY_BONUS = 10

# ===== Railway fix =====
async def on_startup(dp):
    await bot.delete_webhook(drop_pending_updates=True)

# ===== UI =====
def menu(uid, pts):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(f"💰 محفظتي ({pts})", "wallet"),
        InlineKeyboardButton("🎁 مكافأة", "bonus")
    )
    kb.add(
        InlineKeyboardButton("🧩 المهام", "tasks"),
        InlineKeyboardButton("➕ إنشاء مهمة", "create_task")
    )
    kb.add(
        InlineKeyboardButton("💸 سحب", "withdraw"),
        InlineKeyboardButton("🔁 تحويل", "transfer")
    )
    kb.add(
        InlineKeyboardButton("👥 إحالات", "ref")
    )
    if uid in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 الأدمن", "admin"))
    return kb

def withdraw_kb():
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("📱 Vodafone", "w_voda"),
        InlineKeyboardButton("💳 Binance", "w_binance"),
        InlineKeyboardButton("💼 TON", "w_ton")
    )
    return kb

# ===== START =====
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    u = get_user(m.from_user.id, m.from_user.username)

    args = m.get_args()
    if args.isdigit():
        ref = int(args)
        if ref != m.from_user.id:
            if set_ref(m.from_user.id, ref):
                add_points(ref, 10)

    await m.answer("🚀 أهلاً بيك", reply_markup=menu(m.from_user.id, u[2]))

# ===== CALLBACK =====
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()
    uid = c.from_user.id
    u = get_user(uid, c.from_user.username)

    if c.data == "wallet":
        return await c.message.answer(f"💰 {u[2]} نقطة\n💵 {u[2]*RATE:.2f}$")

    if c.data == "bonus":
        if int(time.time()) - u[3] < 86400:
            return await c.message.answer("⏳ كل 24 ساعة")
        add_points(uid, DAILY_BONUS)
        set_bonus(uid)
        return await c.message.answer("🎁 تم")

    if c.data == "tasks":
        tasks = get_active_tasks()
        if not tasks:
            return await c.message.answer("❌ لا يوجد مهام")
        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 تنفيذ", callback_data=f"do_{t[0]}"))
            await c.message.answer(f"{t[2]}\n{t[3]}\n💰 {t[4]}", reply_markup=kb)

    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])
        if is_done(uid, tid):
            return await c.message.answer("❌ خلصتها")
        t = get_task(tid)
        if not t:
            return
        mark_done(uid, tid)
        add_points(uid, t[4])
        return await c.message.answer(f"+{t[4]} نقطة")

    if c.data == "create_task":
        STATE[uid] = "task"
        return await c.message.answer("✍ عنوان | رابط | مكافأة | عدد")

    if c.data == "withdraw":
        return await c.message.answer("💸 اختر الطريقة", reply_markup=withdraw_kb())

    if c.data.startswith("w_"):
        STATE[uid] = c.data
        return await c.message.answer("📥 اكتب الحساب")

    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("✍ @username 50")

    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        return await c.message.answer(f"{link}\n+10 لكل شخص")

    if c.data == "admin":
        return await c.message.answer("🛠 لوحة الأدمن")

# ===== TEXT =====
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid, m.from_user.username)

    if uid in STATE:

        # CREATE TASK
        if STATE[uid] == "task":
            try:
                title, link, reward, count = [x.strip() for x in m.text.split("|")]
                reward = int(reward)
                count = int(count)
            except:
                return await m.answer("❌ صيغة غلط")

            cost = reward * count
            if u[2] < cost:
                return await m.answer("❌ نقاطك مش كفاية")

            add_points(uid, -cost)
            add_task(uid, title, link, reward, count)
            STATE.pop(uid)
            return await m.answer("✅ تم")

        # WITHDRAW
        if STATE[uid].startswith("w_"):
            if u[2] < MIN_WITHDRAW:
                return await m.answer("❌ الحد الأدنى")
            method = STATE[uid].replace("w_", "")
            create_withdraw(uid, u[2]*RATE, method, m.text)
            STATE.pop(uid)
            return await m.answer("✅ تم طلب السحب")

        # TRANSFER
        if STATE[uid] == "transfer":
            try:
                username, amount = m.text.split()
                amount = int(amount)
            except:
                return await m.answer("❌ الصيغة غلط")

            target = get_user_by_username(username)
            if not target:
                return await m.answer("❌ المستخدم مش موجود")

            if u[2] < amount:
                return await m.answer("❌ رصيدك مش كفاية")

            add_points(uid, -amount)
            add_points(target[0], amount)

            STATE.pop(uid)

            return await m.answer("✅ تم التحويل")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
