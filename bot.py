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
def main_menu(user_id, points):
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton(f"💰 محفظتي ({points})", "wallet"),
        InlineKeyboardButton("🎁 مكافأة يومية", "bonus")
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
    if user_id in ADMIN_IDS:
        kb.add(InlineKeyboardButton("🛠 الأدمن", "admin"))
    return kb

def withdraw_methods_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📱 Vodafone", "w_voda"),
        InlineKeyboardButton("💳 Binance", "w_binance")
    )
    kb.add(InlineKeyboardButton("💼 TON", "w_ton"))
    return kb

def admin_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📊 إحصائيات", "a_stats"),
        InlineKeyboardButton("💸 طلبات السحب", "a_withdraws")
    )
    return kb

# ===== START + REF =====
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    args = m.get_args()
    u = get_user(m.from_user.id)

    # referral (once)
    if args.isdigit():
        ref = int(args)
        if ref != m.from_user.id:
            if set_ref(m.from_user.id, ref):
                add_points(ref, 10)

    await m.answer(
        "👋 أهلاً بك في المنصة\n💰 اجمع نقاط وحوّلها لأرباح",
        reply_markup=main_menu(m.from_user.id, u[1])
    )

# ===== CALLBACK =====
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()
    uid = c.from_user.id
    u = get_user(uid)

    # WALLET
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 نقاطك: {u[1]}\n💵 القيمة التقريبية: {u[1]*RATE:.2f}$"
        )

    # BONUS
    if c.data == "bonus":
        now = int(time.time())
        if now - u[2] < 86400:
            return await c.message.answer("⏳ متاح كل 24 ساعة")
        add_points(uid, DAILY_BONUS)
        set_bonus(uid)
        return await c.message.answer(f"🎁 +{DAILY_BONUS} نقطة")

    # TASKS LIST
    if c.data == "tasks":
        tasks = get_active_tasks()
        if not tasks:
            return await c.message.answer("❌ لا توجد مهام حالياً")
        for t in tasks:
            # t: (id, owner, title, link, reward, max_workers, done_count, active)
            kb = InlineKeyboardMarkup()
            kb.add(InlineKeyboardButton("🚀 تنفيذ", callback_data=f"do_{t[0]}"))
            await c.message.answer(
                f"🧩 {t[2]}\n🔗 {t[3]}\n💰 {t[4]} نقطة\n👥 {t[6]}/{t[5]}",
                reply_markup=kb
            )

    # DO TASK
    if c.data.startswith("do_"):
        tid = int(c.data.split("_")[1])
        t = get_task(tid)
        if not t or t[7] == 0 or t[6] >= t[5]:
            return await c.message.answer("❌ المهمة غير متاحة")
        if is_done(uid, tid):
            return await c.message.answer("❌ نفذتها من قبل")
        ok = mark_done(uid, tid)
        if ok:
            add_points(uid, t[4])
            return await c.message.answer(f"🎉 تم التنفيذ +{t[4]} نقطة")
        return await c.message.answer("❌ حدث خطأ")

    # CREATE TASK
    if c.data == "create_task":
        STATE[uid] = "create_task"
        return await c.message.answer(
            "✍ اكتب:\nالعنوان | الرابط | المكافأة | عدد المنفذين\n\n"
            "مثال:\nاشتراك بالقناة | https://t.me/xxx | 5 | 50"
        )

    # WITHDRAW
    if c.data == "withdraw":
        return await c.message.answer(
            f"💸 السحب\n🔻 الحد الأدنى: {MIN_WITHDRAW} نقطة",
            reply_markup=withdraw_methods_kb()
        )

    if c.data.startswith("w_"):
        STATE[uid] = c.data
        return await c.message.answer("📥 اكتب رقمك/عنوانك:")

    # TRANSFER
    if c.data == "transfer":
        STATE[uid] = "transfer"
        return await c.message.answer("✍ اكتب: @username 50")

    # REF
    if c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={uid}"
        return await c.message.answer(
            "👥 نظام الإحالات\n"
            f"{link}\n\n💰 +10 لكل مستخدم جديد"
        )

    # ADMIN
    if c.data == "admin":
        return await c.message.answer("🛠 لوحة الأدمن", reply_markup=admin_kb())

    if c.data == "a_stats":
        cur.execute("SELECT COUNT(*) FROM users")
        users = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM tasks")
        tasks = cur.fetchone()[0]
        return await c.message.answer(f"👥 Users: {users}\n🧩 Tasks: {tasks}")

    if c.data == "a_withdraws":
        ws = get_pending_withdraws()
        if not ws:
            return await c.message.answer("❌ لا يوجد طلبات")
        for w in ws:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton("✅ قبول", callback_data=f"ok_{w[0]}"),
                InlineKeyboardButton("❌ رفض", callback_data=f"no_{w[0]}")
            )
            await c.message.answer(
                f"💸 ID:{w[0]}\n👤 {w[1]}\n💵 {w[2]}$\n📌 {w[3]}",
                reply_markup=kb
            )

    if c.data.startswith("ok_") and uid in ADMIN_IDS:
        wid = int(c.data.split("_")[1])
        set_withdraw_status(wid, "approved")
        return await c.message.answer("✅ تم القبول")

    if c.data.startswith("no_") and uid in ADMIN_IDS:
        wid = int(c.data.split("_")[1])
        set_withdraw_status(wid, "rejected")
        return await c.message.answer("❌ تم الرفض")

# ===== TEXT =====
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # CREATE TASK FLOW
    if uid in STATE and STATE[uid] == "create_task":
        parts = [p.strip() for p in m.text.split("|")]
        if len(parts) != 4:
            return await m.answer("❌ الصيغة: عنوان | رابط | مكافأة | عدد")
        title, link, reward, count = parts
        try:
            reward = int(reward)
            count = int(count)
        except:
            return await m.answer("❌ الأرقام غير صحيحة")

        cost = reward * count
        if u[1] < cost:
            return await m.answer(f"❌ تحتاج {cost} نقطة")

        add_points(uid, -cost)
        add_task(uid, title, link, reward, count)
        STATE.pop(uid)

        return await m.answer("✅ تم نشر المهمة بنجاح")

    # WITHDRAW FLOW
    if uid in STATE and STATE[uid].startswith("w_"):
        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ لم تصل للحد الأدنى")
        method = STATE[uid].replace("w_", "")
        create_withdraw(uid, u[1]*RATE, method, m.text)
        STATE.pop(uid)
        return await m.answer("✅ تم إرسال طلب السحب")

    # TRANSFER
    if uid in STATE and STATE[uid] == "transfer":
        try:
            username, amount = m.text.split()
            amount = int(amount)
            # require username mapping externally if needed
            return await m.answer("⚠️ ربط اليوزر يتطلب حفظ username في الداتابيز")
        except:
            return await m.answer("❌ الصيغة: @username 50")

# ===== RUN =====
if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
