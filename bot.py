import time
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import BOT_TOKEN, ADMIN_IDS
from database import *

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# ================= STATE =================
state = {}
cooldown = {}

# ================= SETTINGS =================
BONUS_AMOUNT = 10
MIN_WITHDRAW = 100
POINT_TO_USD = 0.013
TASK_CREATE_COST = 20

# ================= UI =================
def main_menu(user):
    kb = InlineKeyboardMarkup(row_width=2)

    kb.add(
        InlineKeyboardButton(f"💰 Wallet ({user[1]})", callback_data="wallet"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )

    kb.add(
        InlineKeyboardButton("🧩 Tasks", callback_data="tasks"),
        InlineKeyboardButton("➕ Add Task", callback_data="add_task")
    )

    kb.add(
        InlineKeyboardButton("💸 Withdraw", callback_data="withdraw"),
        InlineKeyboardButton("🔁 Transfer", callback_data="transfer")
    )

    return kb


def admin_menu():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("💸 Withdraws", callback_data="admin_w"),
        InlineKeyboardButton("🧩 Proofs", callback_data="admin_t")
    )
    return kb


# ================= START =================
@dp.message_handler(commands=["start"])
async def start(m: types.Message):
    user = get_user(m.from_user.id)

    if m.from_user.id in ADMIN_IDS:
        return await m.answer("🛠 Admin Panel", reply_markup=admin_menu())

    await m.answer("🚀 Welcome to Platform", reply_markup=main_menu(user))


# ================= CALLBACK =================
@dp.callback_query_handler()
async def cb(c: types.CallbackQuery):
    await c.answer()

    u = get_user(c.from_user.id)

    # ================= WALLET =================
    if c.data == "wallet":
        return await c.message.answer(
            f"💰 Points: {u[1]}\n"
            f"👥 Referrals: {u[2]}\n"
            f"💵 Value: {u[1]*POINT_TO_USD:.2f}$"
        )

    # ================= BONUS =================
    elif c.data == "bonus":
        now = int(time.time())

        if now - u[3] < 86400:
            return await c.message.answer("⏳ Bonus available every 24h")

        add_points(c.from_user.id, BONUS_AMOUNT)
        set_bonus(c.from_user.id)

        return await c.message.answer(f"🎁 +{BONUS_AMOUNT} points added")

    # ================= TASKS =================
    elif c.data == "tasks":
        tasks = get_tasks()

        if not tasks:
            return await c.message.answer("❌ No tasks available")

        for t in tasks:
            kb = InlineKeyboardMarkup()
            kb.add(
                InlineKeyboardButton(
                    f"📥 Do Task ({t[3]})",
                    callback_data=f"do_task:{t[0]}"
                )
            )

            await c.message.answer(
                f"🧩 Task #{t[0]}\n"
                f"🔗 {t[2]}\n"
                f"💰 Reward: {t[3]}",
                reply_markup=kb
            )

    # ================= ADD TASK =================
    elif c.data == "add_task":
        state[c.from_user.id] = "task"
        return await c.message.answer(
            f"➕ Send task:\nlink | reward\n\n"
            f"💡 Cost: {TASK_CREATE_COST} points"
        )

    # ================= EXECUTE TASK =================
    elif c.data.startswith("do_task:"):
        task_id = int(c.data.split(":")[1])
        state[c.from_user.id] = f"proof:{task_id}"

        return await c.message.answer("📤 Send proof now")

    # ================= WITHDRAW =================
    elif c.data == "withdraw":
        return await c.message.answer(
            "💸 Withdraw system\n\n"
            "Send:\nmethod address\n\n"
            f"Min: {MIN_WITHDRAW} points"
        )

    # ================= ADMIN =================
    if c.from_user.id in ADMIN_IDS:

        if c.data == "admin_w":
            w = get_withdraws()

            if not w:
                return await c.message.answer("❌ No withdraw requests")

            for i in w:
                await c.message.answer(
                    f"💸 ID: {i[0]}\n"
                    f"Amount: {i[2]}$\n"
                    f"Method: {i[3]}\n"
                    f"/ok_{i[0]} /no_{i[0]}"
                )

        if c.data == "admin_t":
            cur.execute("SELECT * FROM task_proofs WHERE status='pending'")
            proofs = cur.fetchall()

            if not proofs:
                return await c.message.answer("❌ No proofs")

            for p in proofs:
                kb = InlineKeyboardMarkup()
                kb.add(
                    InlineKeyboardButton("✅ Accept", callback_data=f"ap:{p[0]}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"rej:{p[0]}")
                )

                await c.message.answer(
                    f"📌 Proof #{p[0]}\n"
                    f"👤 User: {p[2]}\n"
                    f"📄 {p[3]}",
                    reply_markup=kb
                )

        if c.data.startswith("ap:"):
            pid = int(c.data.split(":")[1])

            cur.execute("SELECT task_id, user_id FROM task_proofs WHERE id=?", (pid,))
            task_id, user_id = cur.fetchone()

            cur.execute("SELECT reward FROM tasks WHERE id=?", (task_id,))
            reward = cur.fetchone()[0]

            add_points(user_id, reward)

            cur.execute("UPDATE task_proofs SET status='approved' WHERE id=?", (pid,))
            conn.commit()

            return await c.message.answer("✅ Approved")

        if c.data.startswith("rej:"):
            pid = int(c.data.split(":")[1])

            cur.execute("UPDATE task_proofs SET status='rejected' WHERE id=?", (pid,))
            conn.commit()

            return await c.message.answer("❌ Rejected")


# ================= TEXT =================
@dp.message_handler()
async def text(m: types.Message):
    uid = m.from_user.id
    u = get_user(uid)

    # ===== COOLDOWN =====
    now = time.time()
    if uid in cooldown and now - cooldown[uid] < 2:
        return
    cooldown[uid] = now

    # ================= TASK CREATION =================
    if uid in state and state[uid] == "task":
        try:
            link, reward = m.text.split("|")
            reward = int(reward.strip())

            if u[1] < TASK_CREATE_COST:
                return await m.answer("❌ Not enough points")

            add_points(uid, -TASK_CREATE_COST)
            add_task(uid, link.strip(), reward)

            state.pop(uid)

            return await m.answer("✅ Task created")
        except:
            return await m.answer("❌ format: link | reward")

    # ================= PROOF =================
    if uid in state and state[uid].startswith("proof:"):
        task_id = int(state[uid].split(":")[1])

        cur.execute(
            "INSERT INTO task_proofs (task_id, user_id, proof) VALUES (?, ?, ?)",
            (task_id, uid, m.text)
        )
        conn.commit()

        state.pop(uid)

        return await m.answer("📤 Proof submitted")

    # ================= WITHDRAW =================
    if " " in m.text:
        method, address = m.text.split(" ", 1)

        if u[1] < MIN_WITHDRAW:
            return await m.answer("❌ Not enough points")

        amount = u[1] * POINT_TO_USD

        create_withdraw(uid, amount, method, address)

        return await m.answer("✅ Withdraw request sent")


# ================= RUN =================
executor.start_polling(dp, skip_updates=True)
