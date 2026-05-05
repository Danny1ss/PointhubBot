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
task_data = {}

# ================= UI USER =================
def user_menu():
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
        InlineKeyboardButton("🧩 مهام", callback_data="tasks"),
        InlineKeyboardButton("➕ أضف مهمة", callback_data="add_task")
    )
    kb.add(
        InlineKeyboardButton("📢 إعلان", callback_data="ad")
    )
    return kb


# ================= UI ADMIN =================
def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💸 سحوبات", callback_data="admin_w"),
        InlineKeyboardButton("📢 إعلانات", callback_data="admin_a")
    )
    kb.add(
        InlineKeyboardButton("🧩 مهام", callback_data="admin_t")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 لوحة الأدمن", reply_markup=admin_menu())

    await m.answer("👋 أهلاً بك", reply_markup=user_menu())


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

        await c.message.answer("🎁 تم إضافة المكافأة")

    elif c.data == "ref":
        link = f"https://t.me/{(await bot.get_me()).username}?start={c.from_user.id}"
        await c.message.answer(
            f"🔗 رابطك:\n{link}\n"
            f"🎁 لكل إحالة +{REFERRAL_BONUS}"
        )

    elif c.data == "withdraw":
        await c.message.answer("💸 اختر طريقة السحب")

    # 🧩 TASKS
    elif c.data == "tasks":
        tasks = get_tasks()
        if not tasks:
            return await c.message.answer("❌ لا توجد مهام حالياً")

        text = "🧩 المهام المتاحة:\n\n"
        for t in tasks:
            text += f"📌 {t[1]} (+{t[2]} نقاط)\n"

        await c.message.answer(text)

    # ➕ ADD TASK
    elif c.data == "add_task":
        user_state[c.from_user.id] = "task"
        await c.message.answer("✍️ اكتب المهمة بالشكل:\nالرابط | النقاط")

    # ===== ADMIN =====
    if c.from_user.id not in ADMIN_IDS:
        return

    if c.data == "admin_w":
        data = get_withdraws()
        for w in data:
            await c.message.answer(
                f"💸 {w[0]} | {w[2]}$ | {w[3]}\n"
                f"/ok_{w[0]} /no_{w[0]}"
            )

    elif c.data == "admin_t":
        await c.message.answer("🧩 المهام تحت الإدارة")


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
            return await m.answer("📢 تم نشر الإعلان")

    # ===== WITHDRAW FIX =====
    if " " in m.text:
        method, address = m.text.split(" ", 1)

        if u[1] < MIN_WITHDRAW:
            return await m.answer(
                "❌ الحد الأدنى للسحب 100 نقطة\n"
                f"💰 نقاطك الحالية: {u[1]}"
            )

        amount = round(u[1] * 0.013, 2)

        create_withdraw(uid, amount, method, address)

        return await m.answer("✅ تم إرسال طلب السحب")

    # ===== ADD TASK FLOW =====
    if uid in user_state and user_state[uid] == "task":
        try:
            link, points = m.text.split("|")
            add_task(link.strip(), int(points))
            user_state.pop(uid)

            return await m.answer("✅ تم إضافة المهمة")
        except:
            return await m.answer("❌ الصيغة غلط: الرابط | النقاط")


# ================= RUN =================
executor.start_polling(dp)
