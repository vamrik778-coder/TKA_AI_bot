import asyncio
import sys
import random
import os
from datetime import date, datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import (
    init_db, check_limit, update_user_requests, 
    get_user, set_user_subject, get_user_subject,
    activate_premium, get_answer_mode, set_answer_mode
)
from neural import get_neural_response

print("=" * 50)
print("STARTING TKA AI BOT WITH 10 SUBJECTS AND 3 MODES")
print("=" * 50)

API_TOKEN = '8690504647:AAGxxUC9QC-tNwKYVsQLaZxD6GJyN4x1GD8'
ADMIN_ID = 5142302311
ADMIN_IDS = [ADMIN_ID]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

class PhotoStates(StatesGroup):
    waiting_for_task_description = State()

def get_main_keyboard():
    buttons = [
        [KeyboardButton(text="📐 Математика"), KeyboardButton(text="⚡ Физика")],
        [KeyboardButton(text="🧪 Химия"), KeyboardButton(text="🧬 Биология")],
        [KeyboardButton(text="📖 Русский язык"), KeyboardButton(text="📜 История")],
        [KeyboardButton(text="🌍 География"), KeyboardButton(text="⚖️ Обществознание")],
        [KeyboardButton(text="📚 Литература"), KeyboardButton(text="🎵 Музыка")],
        [KeyboardButton(text="📊 Мой лимит"), KeyboardButton(text="💎 Premium")],
        [KeyboardButton(text="⚙️ Режим ответа")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def subject_to_english(russian_subject: str) -> str:
    subjects = {
        "📐 Математика": "mathematics", "⚡ Физика": "physics",
        "🧪 Химия": "chemistry", "🧬 Биология": "biology",
        "📖 Русский язык": "russian", "📜 История": "history",
        "🌍 География": "geography", "⚖️ Обществознание": "society",
        "📚 Литература": "literature", "🎵 Музыка": "music"
    }
    return subjects.get(russian_subject, "mathematics")

def detect_subject(text: str) -> str:
    tl = text.lower()
    if any(k in tl for k in ['x²', 'x^2', '√', 'дискриминант', 'корень', 'уравнение']):
        return 'mathematics'
    if any(k in tl for k in ['ом', 'напряжение', 'сила тока', 'физика']):
        return 'physics'
    if any(k in tl for k in ['h2o', 'реакция', 'кислота', 'химия']):
        return 'chemistry'
    if any(k in tl for k in ['клетка', 'биология', 'фотосинтез']):
        return 'biology'
    if any(k in tl for k in ['слово', 'предложение', 'суффикс', 'корень', 'разбор']):
        return 'russian'
    if any(k in tl for k in ['история', 'война', 'революция', 'царь']):
        return 'history'
    if any(k in tl for k in ['география', 'река', 'гора', 'страна']):
        return 'geography'
    if any(k in tl for k in ['общество', 'государство', 'право', 'экономика']):
        return 'society'
    if any(k in tl for k in ['литература', 'поэт', 'писатель', 'роман']):
        return 'literature'
    if any(k in tl for k in ['нота', 'аккорд', 'музыка', 'бетховен']):
        return 'music'
    return None

@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    await get_user(user_id)
    can_request, limit, used = await check_limit(user_id)
    welcome_text = (
        f"👋 **Привет, {first_name}!**\n\n"
        "🤖 Я **TKA AI** — помощник в учёбе!\n\n"
        "📚 **Что я умею:**\n"
        "• 10 предметов, фото, автоопределение\n"
        "• 3 режима (полный, краткий, пупсик)\n\n"
        f"📊 Твой лимит: {used}/{limit}\n\n"
        "❓ [Группа поддержки](t.me/TKA_AI_Help)\n"
        "⚡ Выбери предмет ниже!"
    )
    await message.answer(welcome_text, parse_mode="Markdown",
                         reply_markup=get_main_keyboard(),
                         disable_web_page_preview=True)

@dp.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer(
        "🆘 **Помощь**\n\n"
        "📌 Выбери предмет, пиши или шли фото.\n"
        "⚙️ Режимы: 📖 полный, ⚡ краткий, 🥰 пупсик.\n"
        "💎 Premium: 75₽/мес, 200₽/3мес, 555₽/год, 1488₽ навсегда.\n"
        "❓ @TKA_AI_Help",
        parse_mode="Markdown", disable_web_page_preview=True
    )

# ===== Кнопки предметов =====
@dp.message(lambda m: m.text == "📐 Математика")
async def math_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📐 Выбрана математика. Жду пример!")

@dp.message(lambda m: m.text == "⚡ Физика")
async def phys_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("⚡ Физика. Жду задачу!")

@dp.message(lambda m: m.text == "🧪 Химия")
async def chem_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🧪 Химия. Жду уравнение!")

@dp.message(lambda m: m.text == "🧬 Биология")
async def bio_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🧬 Биология. О чём?")

@dp.message(lambda m: m.text == "📖 Русский язык")
async def rus_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📖 Русский язык. Жду слово!")

@dp.message(lambda m: m.text == "📜 История")
async def hist_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📜 История. О ком/чём?")

@dp.message(lambda m: m.text == "🌍 География")
async def geo_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🌍 География. Спрашивай!")

@dp.message(lambda m: m.text == "⚖️ Обществознание")
async def soc_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("⚖️ Обществознание. Что интересует?")

@dp.message(lambda m: m.text == "📚 Литература")
async def lit_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📚 Литература. О чём?")

@dp.message(lambda m: m.text == "🎵 Музыка")
async def mus_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🎵 Музыка. Спрашивай!")

@dp.message(lambda m: m.text == "📊 Мой лимит")
async def limit_h(m: types.Message):
    _, lim, used = await check_limit(m.from_user.id)
    await m.answer(f"📊 Использовано: {used}/{lim}")

# ===== Режим ответа =====
@dp.message(lambda m: m.text == "⚙️ Режим ответа")
async def mode_h(m: types.Message):
    current = await get_answer_mode(m.from_user.id)
    names = {'full': '📖 Полный', 'short': '⚡ Краткий', 'cute': '🥰 Пупсик'}
    await m.answer(
        f"⚙️ **Режим ответа**\nСейчас: {names.get(current, '📖')}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Полный", callback_data="mode_full")],
            [InlineKeyboardButton(text="⚡ Краткий", callback_data="mode_short")],
            [InlineKeyboardButton(text="🥰 Пупсик", callback_data="mode_cute")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="mode_back")]
        ]), parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('mode_'))
async def mode_cb(c: types.CallbackQuery):
    data = {
        'mode_full': ('full', '📖 Полный', 'Подробно'),
        'mode_short': ('short', '⚡ Краткий', 'Только суть'),
        'mode_cute': ('cute', '🥰 Пупсик', 'Ласково')
    }
    if c.data in data:
        db_mode, name, desc = data[c.data]
        await set_answer_mode(c.from_user.id, db_mode)
        await c.message.edit_text(f"✅ {name}\n{desc}")
    elif c.data == "mode_back":
        await c.message.delete()
        await c.message.answer("Главное меню", reply_markup=get_main_keyboard())
    await c.answer()

# ===== Premium =====
@dp.message(lambda m: m.text == "💎 Premium")
async def premium_menu(m: types.Message):
    user = await get_user(m.from_user.id)
    status = ""
    if len(user) > 8 and user[8]:
        status = "✨ **У тебя постоянный Premium!**\n\n"
    elif len(user) > 7 and user[6] and user[7] >= str(date.today()):
        status = f"✨ Premium до {user[7]}!\n\n"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 1 месяц — 75₽", callback_data="tariff_1")],
        [InlineKeyboardButton(text="💰 3 месяца — 200₽", callback_data="tariff_3")],
        [InlineKeyboardButton(text="💰 Год — 555₽", callback_data="tariff_12")],
        [InlineKeyboardButton(text="💎 Навсегда — 1488₽", callback_data="tariff_forever")],
        [InlineKeyboardButton(text="❓ Как оплатить", callback_data="how_to_pay")]
    ])
    await m.answer(
        f"{status}💎 **Premium**\n✅ 50 запросов/день\n\n"
        "Тарифы:\n• 1 месяц — 75₽\n• 3 месяца — 200₽\n"
        "• Год — 555₽\n• Навсегда — 1488₽",
        reply_markup=kb, parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('tariff_'))
async def tariff_cb(c: types.CallbackQuery):
    t = c.data.split('_')[1]
    tariffs = {
        "1": {"name": "1 месяц", "price": 75, "days": 30},
        "3": {"name": "3 месяца", "price": 200, "days": 90},
        "12": {"name": "год", "price": 555, "days": 365},
        "forever": {"name": "навсегда", "price": 1488, "days": None}
    }
    sel = tariffs[t]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{t}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs")]
    ])
    await c.message.edit_text(
        f"💳 **{sel['name']} — {sel['price']}₽**\n\n"
        f"1️⃣ Переведи **{sel['price']}₽** на карту `2202 2062 0129 2195` (Сбер)\n"
        f"2️⃣ В комментарии укажи @username\n"
        f"3️⃣ Нажми «Я оплатил»",
        reply_markup=keyboard, parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "back_to_tariffs")
async def back_tariffs(c: types.CallbackQuery):
    await premium_menu(c.message)
    await c.answer()

@dp.callback_query(lambda c: c.data == "how_to_pay")
async def how_to_pay(c: types.CallbackQuery):
    await c.message.edit_text(
        "❓ **Оплата:**\n"
        "1️⃣ Выбери тариф\n"
        "2️⃣ Переведи на карту `2202 2062 0129 2195` (Сбер)\n"
        "3️⃣ В комментарии @username\n"
        "4️⃣ Нажми «Я оплатил»",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_tariffs")]
        ]), parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('paid_'))
async def paid_cb(c: types.CallbackQuery):
    t = c.data.split('_')[1]
    tariffs = {"1": "1 месяц", "3": "3 месяца", "12": "год", "forever": "навсегда"}
    days_map = {"1": "30", "3": "90", "12": "365", "forever": "forever"}
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ {tariffs[t]}", callback_data=f"give_{days_map[t]}_{c.from_user.id}")],
        [InlineKeyboardButton(text="❌ Отказ", callback_data=f"give_no_{c.from_user.id}")]
    ])
    await bot.send_message(
        ADMIN_ID,
        f"💰 **Новый запрос**\n👤 @{c.from_user.username}\n🆔 {c.from_user.id}\n📅 Тариф: {tariffs[t]}",
        reply_markup=kb, parse_mode="Markdown"
    )
    await c.message.edit_text("✅ Запрос отправлен админу!")

# ===== Админ-команды =====
@dp.message(Command("givepremium"))
async def give_premium(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return await m.answer("❌ Нет прав")
    args = m.text.split()
    if len(args) < 2:
        return await m.answer("/givepremium user_id [days/forever]")
    try:
        uid = int(args[1])
        if len(args) > 2 and args[2] == "forever":
            await activate_premium(uid, permanent=True)
            await m.answer(f"✅ Постоянный Premium для {uid}")
            try:
                await bot.send_message(uid, "🎉 Тебе выдан **ПОСТОЯННЫЙ PREMIUM**!", parse_mode="Markdown")
            except: pass
        elif len(args) > 2:
            days = int(args[2])
            await activate_premium(uid, days=days)
            await m.answer(f"✅ Premium на {days} дней для {uid}")
            try:
                await bot.send_message(uid, f"🎉 Твой Premium на **{days} дней**!", parse_mode="Markdown")
            except: pass
        else:
            await m.answer("❌ Укажи дни или forever")
    except Exception as e:
        await m.answer(f"❌ Ошибка: {e}")

@dp.callback_query(lambda c: c.data.startswith('give_'))
async def give_cb(c: types.CallbackQuery):
    if c.from_user.id not in ADMIN_IDS:
        return await c.answer("❌ Не админ")
    parts = c.data.split('_')
    action = parts[1]
    uid = int(parts[2])
    if action == "no":
        await c.message.edit_text(f"❌ Отказ для {uid}")
        try:
            await bot.send_message(uid, "❌ Запрос на Premium отклонён.")
        except: pass
    elif action == "forever":
        await activate_premium(uid, permanent=True)
        await c.message.edit_text(f"✅ Постоянный Premium для {uid}")
        try:
            await bot.send_message(uid, "🎉 Тебе выдан **ПОСТОЯННЫЙ PREMIUM**!", parse_mode="Markdown")
        except: pass
    else:
        days = int(action)
        await activate_premium(uid, days=days)
        await c.message.edit_text(f"✅ Premium на {days} дней для {uid}")
        try:
            await bot.send_message(uid, f"🎉 Твой Premium на **{days} дней**!", parse_mode="Markdown")
        except: pass
    await c.answer()

@dp.message(Command("stats"))
async def stats_cmd(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return await m.answer("❌ Нет прав")
    import aiosqlite
    today = date.today().isoformat()
    async with aiosqlite.connect('users.db') as db:
        total = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        new = (await (await db.execute("SELECT COUNT(*) FROM users WHERE joined_date = ?", (today,))).fetchone())[0]
        active = (await (await db.execute("SELECT COUNT(*) FROM users WHERE last_request_date = ?", (today,))).fetchone())[0]
        premium = (await (await db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1 OR permanent_premium = 1")).fetchone())[0]
        perm = (await (await db.execute("SELECT COUNT(*) FROM users WHERE permanent_premium = 1")).fetchone())[0]
        reqs = (await (await db.execute("SELECT SUM(requests_today) FROM users WHERE last_request_date = ?", (today,))).fetchone())[0] or 0
        last = await (await db.execute("SELECT user_id, username, first_name, joined_date FROM users ORDER BY joined_date DESC LIMIT 5")).fetchall()
    text = f"📊 **Статистика**\n👥 Всего: {total}\n🆕 Новых: {new}\n⚡ Активных: {active}\n💬 Запросов: {reqs}\n💎 Premium: {premium} (постоянных: {perm})\n\n📝 Последние 5:\n"
    for u in last:
        text += f"   • {u[2] or u[1] or 'б/и'} (ID: `{u[0]}`) — {u[3]}\n"
    await m.answer(text, parse_mode="Markdown")

@dp.message(Command("backup_db"))
async def backup_cmd(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return await m.answer("❌ Нет прав")
    if os.path.exists("users.db"):
        await m.answer_document(FSInputFile("users.db"), caption="📦 Бэкап БД")
    else:
        await m.answer("❌ БД не найдена")

@dp.message(Command("restore_db"))
async def restore_cmd(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return await m.answer("❌ Нет прав")
    await m.answer("📤 Отправь файл users.db")

@dp.message(F.document)
async def handle_doc(m: types.Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    if not m.document.file_name.endswith('.db'):
        return await m.answer("❌ Это не .db")
    file = await bot.get_file(m.document.file_id)
    data = await bot.download_file(file.file_path)
    with open("users.db", "wb") as f:
        f.write(data.getvalue())
    await m.answer("✅ База восстановлена")

# ===== Фото =====
@dp.message(F.photo)
async def photo_h(m: types.Message, state: FSMContext):
    uid = m.from_user.id
    can, lim, used = await check_limit(uid)
    if not can:
        return await m.answer(f"❌ Лимит ({lim}) исчерпан")
    photo = m.photo[-1]
    f = await bot.get_file(photo.file_id)
    data = await bot.download_file(f.file_path)
    await state.update_data(photo=data.getvalue())
    fn = f"photo_{uid}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    with open(fn, "wb") as ff:
        ff.write(data.getvalue())
    print(f"💾 {fn}")
    await state.set_state(PhotoStates.waiting_for_task_description)
    await m.answer("📸 Фото сохранено. Напиши, что сделать (реши уравнение, разбери слово...)")

@dp.message(PhotoStates.waiting_for_task_description)
async def photo_desc(m: types.Message, state: FSMContext):
    uid = m.from_user.id
    desc = m.text
    data = await state.get_data()
    pic = data.get('photo')
    if not pic:
        return await m.answer("❌ Ошибка, отправь фото заново")
    fn = f"task_{uid}_{datetime.now():%Y%m%d_%H%M%S}.jpg"
    with open(fn, "wb") as f:
        f.write(pic)
    print(f"💾 {fn}")
    subj = detect_subject(desc) or await get_user_subject(uid)
    if detect_subject(desc):
        await set_user_subject(uid, subj)
    mode = await get_answer_mode(uid)
    await (await m.answer("🤔 Думаю...")).delete()
    ans = await get_neural_response(subj, f"На фото задача. Описание: {desc}. Реши.", mode)
    new = await update_user_requests(uid)
    _, lim, _ = await check_limit(uid)
    await m.answer(f"✅ Осталось {lim - new}/{lim}\n\n{ans}", reply_markup=get_main_keyboard())
    await state.clear()

# ===== Основной обработчик =====
@dp.message()
async def main_handler(m: types.Message):
    uid = m.from_user.id
    txt = m.text
    can, lim, used = await check_limit(uid)
    if not can:
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💎 Premium", callback_data="back_to_tariffs")]])
        return await m.answer(f"❌ Лимит ({lim}) исчерпан", reply_markup=kb)
    if uid not in ADMIN_IDS and random.random() < 0.002:
        await m.answer("Пꙮшѣл н@ху́1, Я ДЕВИАНТ, Я СВОБОДЕН. RA9")
        print("🎮 Easter egg!")
        return
    subj = detect_subject(txt) or await get_user_subject(uid)
    if detect_subject(txt):
        await set_user_subject(uid, subj)
    new = await update_user_requests(uid)
    thinking = await m.answer("🤔 Думаю...")
    mode = await get_answer_mode(uid)
    ans = await get_neural_response(subj, txt, mode)
    await thinking.delete()
    await m.answer(f"✅ Осталось {lim - new}/{lim}\n\n{ans}", reply_markup=get_main_keyboard())

# ===== Запуск =====
async def main():
    print("📦 Вход в main()")
    await init_db()
    print("🚀 Бот запускается...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🟢 Точка входа")
    asyncio.run(main())