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

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from holidays import get_today_holiday, get_random_greeting_style

from database import (
    init_db, check_limit, update_user_requests,
    get_user, set_user_subject, get_user_subject,
    activate_premium, get_answer_mode, set_answer_mode,
    check_image_limit, update_image_counter
)
from neural import get_neural_response
from nanobanana import NanoBananaAPI

print("=" * 50)
print("🚀 STARTING TKA AI BOT WITH 10 SUBJECTS, 3 MODES, HOLIDAYS, IMAGE GENERATION")
print("=" * 50)

# ========== НАСТРОЙКИ ==========
API_TOKEN = '8690504647:AAGxxUC9QC-tNwKYVsQLaZxD6GJyN4x1GD8'
ADMIN_ID = 5142302311
ADMIN_IDS = [ADMIN_ID]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ===== ИНИЦИАЛИЗАЦИЯ NANO BANANA =====
nano = NanoBananaAPI()

# ========== СОСТОЯНИЯ ==========
class PhotoStates(StatesGroup):
    waiting_for_task_description = State()

class GreetStates(StatesGroup):
    waiting_for_prompt = State()

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    """Главная клавиатура с кнопками категорий"""
    buttons = [
        [KeyboardButton(text="🎓 Предметы"), KeyboardButton(text="📊 Мой лимит")],
        [KeyboardButton(text="💎 Premium"), KeyboardButton(text="⚙️ Режим ответа")],
        [KeyboardButton(text="🎉 Праздник сегодня"), KeyboardButton(text="🎭 Поздравь")],
        [KeyboardButton(text="🎨 Нарисовать картинку"), KeyboardButton(text="📋 Мои команды")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_subjects_keyboard():
    """Клавиатура со всеми предметами"""
    buttons = [
        [KeyboardButton(text="📐 Математика"), KeyboardButton(text="⚡ Физика"), KeyboardButton(text="🧪 Химия")],
        [KeyboardButton(text="🧬 Биология"), KeyboardButton(text="📖 Русский язык"), KeyboardButton(text="📜 История")],
        [KeyboardButton(text="🌍 География"), KeyboardButton(text="⚖️ Обществознание"), KeyboardButton(text="📚 Литература")],
        [KeyboardButton(text="🎵 Музыка"), KeyboardButton(text="🔙 Назад в главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========
def subject_to_english(russian_subject: str) -> str:
    """Переводит название предмета на английский для базы данных"""
    subjects = {
        "📐 Математика": "mathematics",
        "⚡ Физика": "physics",
        "🧪 Химия": "chemistry",
        "🧬 Биология": "biology",
        "📖 Русский язык": "russian",
        "📜 История": "history",
        "🌍 География": "geography",
        "⚖️ Обществознание": "society",
        "📚 Литература": "literature",
        "🎵 Музыка": "music"
    }
    return subjects.get(russian_subject, "mathematics")

def detect_subject(text: str) -> str:
    """Автоматически определяет предмет по тексту"""
    tl = text.lower()
    
    # Математика
    if any(k in tl for k in ['x²', 'x^2', '√', 'дискриминант', 'корень', 'уравнение']):
        return 'mathematics'
    
    # Физика
    if any(k in tl for k in ['ом', 'напряжение', 'сила тока', 'физика']):
        return 'physics'
    
    # Химия
    if any(k in tl for k in ['h2o', 'реакция', 'кислота', 'химия']):
        return 'chemistry'
    
    # Биология
    if any(k in tl for k in ['клетка', 'биология', 'фотосинтез', 'организм']):
        return 'biology'
    
    # Русский язык
    if any(k in tl for k in ['слово', 'предложение', 'суффикс', 'корень', 'разбор']):
        return 'russian'
    
    # История
    if any(k in tl for k in ['история', 'война', 'революция', 'царь', 'дата']):
        return 'history'
    
    # География
    if any(k in tl for k in ['география', 'река', 'гора', 'страна', 'столица']):
        return 'geography'
    
    # Обществознание
    if any(k in tl for k in ['общество', 'государство', 'право', 'экономика']):
        return 'society'
    
    # Литература
    if any(k in tl for k in ['литература', 'поэт', 'писатель', 'роман']):
        return 'literature'
    
    # Музыка
    if any(k in tl for k in ['нота', 'аккорд', 'музыка', 'бетховен']):
        return 'music'
    
    return None

# ========== КОМАНДА СТАРТ ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    await get_user(user_id)
    can_request, limit, used = await check_limit(user_id)
    
    welcome_text = (
        f"👋 **Привет, {first_name}!**\n\n"
        "🤖 Я **TKA AI** — твой помощник в учёбе!\n\n"
        "📚 **Что я умею:**\n"
        "• 10 предметов, фото, автоопределение\n"
        "• 3 режима (полный, краткий, пупсик)\n"
        "• 🎉 Поздравляю с праздниками\n"
        "• 🎭 Генерирую поздравления\n"
        "• 🎨 Рисую картинки по тексту\n\n"
        f"📊 Твой лимит: {used}/{limit}\n\n"
        "❓ [Группа поддержки](t.me/TKA_AI_Help)\n"
        "⚡ Выбери предмет ниже или нажми кнопку!"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(),
        disable_web_page_preview=True
    )

# ========== КОМАНДА ПОМОЩИ ==========
@dp.message(Command("help"))
async def help_command(message: types.Message):
    help_text = (
        "🆘 **Помощь**\n\n"
        "📌 Выбери предмет, пиши или шли фото.\n"
        "⚙️ Режимы: 📖 полный, ⚡ краткий, 🥰 пупсик.\n"
        "🎉 Праздники: проверяю сам или по команде `/holiday`\n"
        "🎭 Поздравления: `/greet бабушку с 8 марта`\n"
        "🎨 Генерация: `/draw кот в космосе`\n"
        "💎 Premium: 75₽/мес, 200₽/3мес, 555₽/год, 1488₽ навсегда.\n"
        "❓ @TKA_AI_Help",
        parse_mode="Markdown",
        disable_web_page_preview=True
    )
    await message.answer(help_text, parse_mode="Markdown", disable_web_page_preview=True)

# ========== КОМАНДА СПИСОК КОМАНД ==========
@dp.message(Command("mycommands"))
@dp.message(lambda m: m.text == "📋 Мои команды")
async def user_commands(message: types.Message):
    commands_text = (
        "📋 **Доступные команды**\n\n"
        "👤 **Основные:**\n"
        "/start — запустить бота\n"
        "/help — помощь\n"
        "/mycommands — этот список\n\n"
        "🎨 **Генерация:**\n"
        "/draw [текст] — нарисовать картинку\n"
        "/image [текст] — то же самое\n\n"
        "🎭 **Поздравления:**\n"
        "/greet [текст] — создать поздравление\n"
        "/holiday — какой сегодня праздник\n\n"
        "🎓 **Предметы:**\n"
        "Доступны через кнопку «🎓 Предметы» в меню\n\n"
        "⚙️ **Режимы ответа:**\n"
        "Меняются через кнопку «⚙️ Режим ответа»\n\n"
        "❓ **Вопросы:**\n"
        "[Группа поддержки](t.me/TKA_AI_Help)"
    )
    await message.answer(
        commands_text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# ========== КНОПКИ НАВИГАЦИИ ==========
@dp.message(lambda m: m.text == "🎓 Предметы")
async def subjects_menu(message: types.Message):
    await message.answer(
        "📚 **Выбери предмет:**",
        reply_markup=get_subjects_keyboard(),
        parse_mode="Markdown"
    )

@dp.message(lambda m: m.text == "🔙 Назад в главное меню")
async def back_to_main(message: types.Message):
    await message.answer(
        "🏠 **Главное меню**",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

# ========== ОБРАБОТЧИКИ ПРЕДМЕТОВ ==========
@dp.message(lambda m: m.text == "📐 Математика")
async def math_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📐 Ты выбрал Математику. Напиши пример!", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "⚡ Физика")
async def phys_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("⚡ Физика. Жду задачу!", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "🧪 Химия")
async def chem_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🧪 Химия. Жду уравнение!", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "🧬 Биология")
async def bio_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🧬 Биология. О чём расскажем?", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "📖 Русский язык")
async def rus_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📖 Русский язык. Присылай слово!", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "📜 История")
async def hist_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📜 История. О ком/чём?", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "🌍 География")
async def geo_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🌍 География. Спрашивай!", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "⚖️ Обществознание")
async def soc_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("⚖️ Обществознание. Что интересует?", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "📚 Литература")
async def lit_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("📚 Литература. О чём?", reply_markup=get_main_keyboard())

@dp.message(lambda m: m.text == "🎵 Музыка")
async def mus_h(m: types.Message):
    await set_user_subject(m.from_user.id, subject_to_english(m.text))
    await m.answer("🎵 Музыка. Спрашивай!", reply_markup=get_main_keyboard())

# ========== КНОПКА ЛИМИТА ==========
@dp.message(lambda m: m.text == "📊 Мой лимит")
async def limit_h(m: types.Message):
    _, req_lim, req_used = await check_limit(m.from_user.id)
    img_can, img_lim, img_used = await check_image_limit(m.from_user.id)
    
    await m.answer(
        f"📊 **Твои лимиты на сегодня:**\n\n"
        f"📝 **Запросы:** {req_used}/{req_lim}\n"
        f"🎨 **Картинки:** {img_used}/{img_lim}",
        parse_mode="Markdown"
    )
    # ========== РЕЖИМ ОТВЕТА ==========
@dp.message(lambda m: m.text == "⚙️ Режим ответа")
async def mode_h(m: types.Message):
    current = await get_answer_mode(m.from_user.id)
    names = {'full': '📖 Полный', 'short': '⚡ Краткий', 'cute': '🥰 Пупсик'}
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Полный (подробно)", callback_data="mode_full")],
        [InlineKeyboardButton(text="⚡ Краткий (только суть)", callback_data="mode_short")],
        [InlineKeyboardButton(text="🥰 Пупсик (ласковый)", callback_data="mode_cute")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="mode_back")]
    ])
    
    await m.answer(
        f"⚙️ **Режим ответа**\n\nСейчас выбран: **{names.get(current, '📖 Полный')}**",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('mode_'))
async def mode_cb(c: types.CallbackQuery):
    user_id = c.from_user.id
    
    mode_data = {
        'mode_full': ('full', '📖 Полный', 'Теперь бот будет объяснять подробно, с шагами и примерами.'),
        'mode_short': ('short', '⚡ Краткий', 'Теперь бот будет отвечать только по существу, без лишних объяснений.'),
        'mode_cute': ('cute', '🥰 Пупсик', 'Бот будет милым и ласковым, но в рамках приличия 💕'),
    }
    
    if c.data in mode_data:
        db_mode, display_name, description = mode_data[c.data]
        await set_answer_mode(user_id, db_mode)
        await c.message.edit_text(f"✅ **Режим ответа:** {display_name}\n\n{description}")
    elif c.data == "mode_back":
        await c.message.delete()
        await c.message.answer("🏠 **Главное меню**", reply_markup=get_main_keyboard())
    
    await c.answer()

# ========== ПРАЗДНИКИ ==========
@dp.message(Command("holiday"))
@dp.message(lambda m: m.text == "🎉 Праздник сегодня")
async def holiday_command(message: types.Message):
    holiday = get_today_holiday()
    if holiday:
        await message.answer(
            f"🎉 **Сегодня:** {holiday['name']}!\n\n"
            f"С чем вас и поздравляю! 🥳",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "🍃 Сегодня нет официальных праздников.\n"
            "Но это не повод не улыбнуться! 😊",
            parse_mode="Markdown"
        )

# ========== ПОЗДРАВЛЕНИЯ ==========
@dp.message(Command("greet"))
@dp.message(lambda m: m.text == "🎭 Поздравь")
async def greet_command(message: types.Message, state: FSMContext):
    parts = message.text.split(maxsplit=1)
    
    if len(parts) < 2:
        await message.answer(
            "🎭 **Напиши, кого и с чем поздравить**\n"
            "Например: «бабушку с 8 марта» или «друга с днём рождения»"
        )
        await state.set_state(GreetStates.waiting_for_prompt)
        return
    
    prompt = parts[1]
    await generate_greeting(message, prompt, state)

@dp.message(GreetStates.waiting_for_prompt)
async def process_greeting_prompt(message: types.Message, state: FSMContext):
    await generate_greeting(message, message.text, state)

async def generate_greeting(message: types.Message, prompt: str, state: FSMContext):
    user_id = message.from_user.id
    
    can_request, limit, used = await check_limit(user_id)
    if not can_request:
        await message.answer(f"❌ Лимит ({limit}) на сегодня исчерпан!")
        await state.clear()
        return
    
    thinking = await message.answer("🎭 Придумываю красивое поздравление...")
    
    full_prompt = f"Придумай красивое, душевное поздравление: {prompt}. Используй смайлики, будь оригинальным."
    mode = await get_answer_mode(user_id)
    result = await get_neural_response("russian", full_prompt, mode)
    
    await thinking.delete()
    await message.answer(result, parse_mode="Markdown")
    
    await update_user_requests(user_id)
    await state.clear()

# ========== ГЕНЕРАЦИЯ КАРТИНОК ==========
@dp.message(Command("draw"))
@dp.message(Command("image"))
@dp.message(lambda m: m.text == "🎨 Нарисовать картинку")
async def draw_command(message: types.Message):
    user_id = message.from_user.id
    
    if message.text == "🎨 Нарисовать картинку":
        await message.answer(
            "🎨 **Как нарисовать картинку:**\n"
            "Напиши команду:\n"
            "`/draw кот в космосе`\n\n"
            "Или на английском (работает лучше):\n"
            "`/draw cat in space`",
            parse_mode="Markdown"
        )
        return
    
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "❓ **Как пользоваться:**\n"
            "Напиши `/draw кот в космосе`\n"
            "Или на английском: `/draw cat in space` — так работает лучше!",
            parse_mode="Markdown"
        )
        return
    
    prompt = parts[1]
    
    can_gen, limit, used = await check_image_limit(user_id)
    if not can_gen:
        await message.answer(
            f"❌ Лимит ({limit}) на сегодня исчерпан!\n"
            f"Приобрети Premium для 10 картинок в день.",
            reply_markup=get_main_keyboard()
        )
        return
    
    status = await message.answer("🍌 **Nano Banana рисует...** Это займёт 5–10 секунд", parse_mode="Markdown")
    
    image_bytes = await nano.generate_image(prompt)
    
    if image_bytes:
        new_count = await update_image_counter(user_id)
        await status.delete()
        await message.answer_photo(
            photo=image_bytes,
            caption=f"🍌 **Запрос:** {prompt}\n📊 Осталось {limit - new_count}/{limit} генераций",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await status.edit_text(
            "❌ Не удалось сгенерировать картинку.\n"
            "Попробуй другой запрос или напиши на английском."
        )

# ========== PREMIUM МЕНЮ ==========
@dp.message(lambda message: message.text == "💎 Premium")
async def premium_menu(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    status_text = ""
    if len(user) > 8 and user[8]:
        status_text = "✨ **У тебя уже есть ПОСТОЯННЫЙ Premium!**\n\n"
    elif len(user) > 7 and user[6] and user[7] and user[7] >= str(date.today()):
        status_text = f"✨ **У тебя уже есть Premium до {user[7]}!**\n\n"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 1 месяц — 75₽", callback_data="tariff_1")],
        [InlineKeyboardButton(text="💰 3 месяца — 200₽", callback_data="tariff_3")],
        [InlineKeyboardButton(text="💰 Год — 555₽", callback_data="tariff_12")],
        [InlineKeyboardButton(text="💎 Навсегда — 1488₽", callback_data="tariff_forever")],
        [InlineKeyboardButton(text="❓ Как оплатить", callback_data="how_to_pay")]
    ])

    await message.answer(
        f"{status_text}"
        "💎 **Premium подписка** 💎\n\n"
        "✅ 50 запросов в день\n"
        "✅ 10 генераций картинок в день\n"
        "⚡ Приоритетная скорость\n"
        "📚 Доступ ко всем предметам\n\n"
        "💰 **Тарифы:**\n"
        "• 1 месяц — 75₽\n"
        "• 3 месяца — 200₽\n"
        "• Год — 555₽\n"
        "• Навсегда — 1488₽\n\n"
        "Выбери тариф:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('tariff_'))
async def tariff_selected(callback: types.CallbackQuery):
    tariff = callback.data.split('_')[1]
    tariffs = {
        "1": {"name": "1 месяц", "price": 75, "days": 30},
        "3": {"name": "3 месяца", "price": 200, "days": 90},
        "12": {"name": "год", "price": 555, "days": 365},
        "forever": {"name": "навсегда", "price": 1488, "days": None}
    }
    selected = tariffs[tariff]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{tariff}")],
        [InlineKeyboardButton(text="🔙 Назад к тарифам", callback_data="back_to_tariffs")]
    ])

    await callback.message.edit_text(
        f"💳 **Оплата тарифа {selected['name']} — {selected['price']}₽**\n\n"
        f"1️⃣ Переведи **{selected['price']}₽** на карту:\n"
        "`2202 2062 0129 2195` (Сбер)\n\n"
        "2️⃣ В комментарии к переводу укажи свой **@username**\n\n"
        "3️⃣ После перевода нажми кнопку **«Я оплатил»**\n\n"
        "⏳ Админ проверит перевод и активирует Premium в течение 24 часов.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data == "back_to_tariffs")
async def back_to_tariffs(callback: types.CallbackQuery):
    await premium_menu(callback.message)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "how_to_pay")
async def how_to_pay(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к тарифам", callback_data="back_to_tariffs")]
    ])

    await callback.message.edit_text(
        "❓ **Как оплатить Premium**\n\n"
        "1️⃣ Выбери тариф\n"
        "2️⃣ Переведи сумму на карту `2202 2062 0129 2195` (Сбер)\n"
        "3️⃣ В комментарии укажи @username\n"
        "4️⃣ Нажми кнопку **«Я оплатил»**\n\n"
        "⏳ Админ проверит в течение 24 часов.",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('paid_'))
async def process_paid(callback: types.CallbackQuery):
    tariff = callback.data.split('_')[1]
    user_id = callback.from_user.id
    username = callback.from_user.username or "нет юзернейма"
    first_name = callback.from_user.first_name

    tariffs = {
        "1": {"name": "1 месяц", "days": 30},
        "3": {"name": "3 месяца", "days": 90},
        "12": {"name": "год", "days": 365},
        "forever": {"name": "навсегда", "days": None}
    }
    selected = tariffs[tariff]

    if selected["days"]:
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ {selected['name']}", callback_data=f"give_{selected['days']}_{user_id}")],
            [InlineKeyboardButton(text="❌ Отказ", callback_data=f"give_no_{user_id}")]
        ])
    else:
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Навсегда", callback_data=f"give_forever_{user_id}")],
            [InlineKeyboardButton(text="❌ Отказ", callback_data=f"give_no_{user_id}")]
        ])

    await bot.send_message(
        ADMIN_ID,
        f"💰 **Новый запрос на Premium!**\n\n"
        f"👤 Пользователь: @{username}\n"
        f"🆔 ID: {user_id}\n"
        f"📝 Имя: {first_name}\n"
        f"📅 Тариф: {selected['name']}\n\n"
        f"Проверь перевод в банке и нажми кнопку:",
        reply_markup=admin_keyboard,
        parse_mode="Markdown"
    )

    await callback.message.edit_text(
        "✅ **Запрос отправлен!**\n\n"
        "Админ проверит перевод и активирует Premium в течение 24 часов.\n"
        "Спасибо за поддержку! 🙏",
        parse_mode="Markdown"
    )

# ========== АДМИН-КОМАНДЫ ==========
@dp.message(Command("givepremium"))
async def give_premium_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer(
            "❌ Использование:\n"
            "/givepremium user_id days\n"
            "/givepremium user_id forever\n\n"
            "Пример: /givepremium 123456789 30"
        )
        return

    try:
        user_id = int(args[1])

        if len(args) > 2 and args[2] == "forever":
            await activate_premium(user_id, permanent=True)
            await message.answer(f"✅ Постоянный Premium выдан пользователю {user_id}!")
            try:
                await bot.send_message(
                    user_id,
                    "🎉 **ПОЗДРАВЛЯЮ!** 🎉\n\n"
                    "Тебе выдан **ПОСТОЯННЫЙ PREMIUM ДОСТУП**!\n"
                    "Спасибо за поддержку проекта! 💪",
                    parse_mode="Markdown"
                )
            except:
                await message.answer("⚠️ Пользователь не найден или заблокировал бота")

        elif len(args) > 2:
            days = int(args[2])
            await activate_premium(user_id, days=days)
            await message.answer(f"✅ Premium на {days} дней выдан пользователю {user_id}!")
            try:
                await bot.send_message(
                    user_id,
                    f"🎉 **Поздравляю!** 🎉\n\n"
                    f"Твой Premium активирован на **{days} дней**!\n"
                    f"Спасибо за поддержку проекта! 💪",
                    parse_mode="Markdown"
                )
            except:
                await message.answer("⚠️ Пользователь не найден или заблокировал бота")
        else:
            await message.answer("❌ Укажи количество дней или 'forever'")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.callback_query(lambda c: c.data.startswith('give_'))
async def admin_give_callback(callback: types.CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Ты не админ!")
        return

    parts = callback.data.split('_')
    action = parts[1]
    user_id = int(parts[2])

    if action == "no":
        await callback.message.edit_text(f"❌ Запрос для пользователя {user_id} отклонён")
        await bot.send_message(
            user_id,
            "❌ К сожалению, твой запрос на Premium отклонён.\n"
            "Проверь правильность перевода или свяжись с админом."
        )
        return

    if action == "forever":
        await activate_premium(user_id, permanent=True)
        text = f"✅ Постоянный Premium выдан пользователю {user_id}!"
        await bot.send_message(
            user_id,
            "🎉 **ПОЗДРАВЛЯЮ!** 🎉\n\n"
            "Тебе выдан **ПОСТОЯННЫЙ PREMIUM ДОСТУП**!\n"
            "Спасибо за поддержку проекта! 💪",
            parse_mode="Markdown"
        )
    else:
        days = int(action)
        await activate_premium(user_id, days=days)
        text = f"✅ Premium на {days} дней выдан пользователю {user_id}!"
        await bot.send_message(
            user_id,
            f"🎉 **Поздравляю!** 🎉\n\n"
            f"Твой Premium активирован на **{days} дней**!\n"
            f"Спасибо за поддержку проекта! 💪",
            parse_mode="Markdown"
        )

    await callback.message.edit_text(text)

# ========== СТАТИСТИКА ==========
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    import aiosqlite
    from datetime import date

    today = date.today().isoformat()

    async with aiosqlite.connect('users.db') as db:
        total = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
        new = (await (await db.execute("SELECT COUNT(*) FROM users WHERE joined_date = ?", (today,))).fetchone())[0]
        active = (await (await db.execute("SELECT COUNT(*) FROM users WHERE last_request_date = ?", (today,))).fetchone())[0]
        premium = (await (await db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1 OR permanent_premium = 1")).fetchone())[0]
        perm = (await (await db.execute("SELECT COUNT(*) FROM users WHERE permanent_premium = 1")).fetchone())[0]
        reqs = (await (await db.execute("SELECT SUM(requests_today) FROM users WHERE last_request_date = ?", (today,))).fetchone())[0] or 0
        last = await (await db.execute("SELECT user_id, username, first_name, joined_date FROM users ORDER BY joined_date DESC LIMIT 5")).fetchall()

    stats_text = (
        "📊 **Статистика бота**\n\n"
        f"👥 **Всего пользователей:** {total}\n"
        f"🆕 **Новых сегодня:** {new}\n"
        f"⚡ **Активных сегодня:** {active}\n"
        f"💬 **Запросов сегодня:** {reqs}\n"
        f"💎 **Premium всего:** {premium}\n"
        f"   ├─ Обычный: {premium - perm}\n"
        f"   └─ Навсегда: {perm}\n\n"
        "📝 **Последние 5 пользователей:**\n"
    )

    for u in last:
        uid, uname, fname, joined = u
        name_display = fname or uname or "без имени"
        stats_text += f"   • {name_display} (ID: `{uid}`) — {joined}\n"

    await message.answer(stats_text, parse_mode="Markdown")

# ========== БЭКАП БАЗЫ ==========
@dp.message(Command("backup_db"))
async def backup_database(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    db_file = "users.db"
    if not os.path.exists(db_file):
        await message.answer("❌ Файл базы данных не найден.")
        return

    await message.answer_document(
        document=FSInputFile(db_file),
        caption="📦 Бэкап базы данных"
    )

@dp.message(Command("restore_db"))
async def restore_database(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    await message.answer("📤 Отправь мне файл базы данных (users.db)")

@dp.message(F.document)
async def handle_db_file(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    document = message.document
    if not document.file_name.endswith('.db'):
        await message.answer("❌ Это не файл базы данных (.db)")
        return

    file_info = await bot.get_file(document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    with open("users.db", "wb") as f:
        f.write(downloaded_file.getvalue())

    await message.answer("✅ База данных успешно восстановлена!")

# ========== ОБРАБОТЧИК ФОТО ==========
@dp.message(F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    print(f"\n📸 ПОЛУЧЕНО ФОТО от {user_id}")

    can_request, limit, used = await check_limit(user_id)
    if not can_request:
        await message.answer(f"❌ Лимит ({limit}) на сегодня исчерпан!")
        return

    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    photo_bytes = downloaded_file.getvalue()

    await state.update_data(photo=photo_bytes)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{user_id}_{timestamp}.jpg"
    with open(filename, "wb") as f:
        f.write(photo_bytes)
    print(f"💾 Фото сохранено как {filename}")

    await state.set_state(PhotoStates.waiting_for_task_description)

    await message.answer(
        "📸 **Фото получено и сохранено!**\n\n"
        "Теперь **напиши, что нужно сделать** с этой задачей:\n"
        "• 'реши уравнение'\n"
        "• 'найди дискриминант'\n"
        "• 'упрости выражение'\n"
        "• 'сделай разбор слова'\n"
        "• или просто опиши словами\n\n"
        "Я запомню фото и решу задачу по твоему описанию!",
        parse_mode="Markdown"
    )

@dp.message(PhotoStates.waiting_for_task_description)
async def process_photo_task(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    task_description = message.text

    data = await state.get_data()
    photo_bytes = data.get('photo')

    if not photo_bytes:
        await message.answer("❌ Что-то пошло не так. Отправь фото заново.")
        await state.clear()
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"task_{user_id}_{timestamp}.jpg"
    with open(filename, "wb") as f:
        f.write(photo_bytes)
    print(f"💾 Фото задачи сохранено как {filename}")

    detected_subject = detect_subject(task_description)
    if detected_subject:
        await set_user_subject(user_id, detected_subject)
        subject_eng = detected_subject
        print(f"🎯 Автоопределение по описанию: {detected_subject}")
    else:
        subject_eng = await get_user_subject(user_id)

    processing = await message.answer("🤔 Анализирую задачу...")

    mode = await get_answer_mode(user_id)
    full_task = f"На фото задача. Описание от пользователя: {task_description}. Реши задачу подробно."
    neural_answer = await get_neural_response(subject_eng, full_task, mode)

    await processing.delete()

    new_count = await update_user_requests(user_id)
    can_request, limit, used = await check_limit(user_id)

    await message.answer(
        f"✅ Осталось {limit - new_count} из {limit}\n\n"
        f"{neural_answer}",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard()
    )

    await state.clear()

# ========== ОСНОВНОЙ ОБРАБОТЧИК ==========
@dp.message()
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    task_text = message.text

    print(f"\n📨 ПОЛУЧЕНО СООБЩЕНИЕ от {user_id}: {task_text}")

    can_request, limit, used = await check_limit(user_id)

    if not can_request:
        print(f"❌ Лимит исчерпан для {user_id}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Купить Premium", callback_data="back_to_tariffs")]
        ])
        await message.answer(
            f"❌ Лимит ({limit}) на сегодня исчерпан!\n"
            f"Приобрети Premium для 50 запросов в день!",
            reply_markup=keyboard
        )
        return

    if message.from_user.id not in ADMIN_IDS and random.random() < 0.002:
        await message.answer("Пꙮшѣл н@ху́1, Я ДЕВИАНТ, Я СВОБОДЕН. RA9")
        print("🎮 Пасхалка сработала!")
        return

    detected_subject = detect_subject(task_text)
    if detected_subject:
        await set_user_subject(user_id, detected_subject)
        subject_eng = detected_subject
        subject_translate = {
            "mathematics": "Математика", "physics": "Физика", "chemistry": "Химия",
            "biology": "Биология", "russian": "Русский язык", "history": "История",
            "geography": "География", "society": "Обществознание",
            "literature": "Литература", "music": "Музыка"
        }
        subject_rus = subject_translate.get(detected_subject, detected_subject)
        print(f"🎯 Автоопределение: {subject_rus}")
    else:
        subject_eng = await get_user_subject(user_id)

    print(f"📚 Использую предмет: {subject_eng}")

    new_count = await update_user_requests(user_id)
    print(f"📊 Счётчик: {new_count}/{limit}")

    thinking_msg = await message.answer("🤔 Думаю...")
    mode = await get_answer_mode(user_id)
    neural_answer = await get_neural_response(subject_eng, task_text, mode)

    await thinking_msg.delete()

    await message.answer(
        f"✅ Осталось {limit - new_count} из {limit}\n\n"
        f"{neural_answer}",
        reply_markup=get_main_keyboard()
    )

# ========== ПЛАНИРОВЩИК ПРАЗДНИКОВ ==========
async def send_holiday_greeting():
    print(f"🔔 Проверяем праздники на {datetime.now().strftime('%d.%m.%Y')}...")

    holiday = get_today_holiday()
    if not holiday:
        print("  Сегодня нет праздников")
        return

    holiday_name = holiday["name"]
    style_key = holiday["style_key"]
    random_epithet = get_random_greeting_style(style_key)

    print(f"🎉 СЕГОДНЯ ПРАЗДНИК: {holiday_name}")

    import aiosqlite
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute("SELECT user_id FROM users")
        users = await cursor.fetchall()

    greeting_text = (
        f"🎊 **{random_epithet.title()} {holiday_name}!** 🎊\n\n"
        f"✨ Пусть этот день подарит радость и улыбки!\n"
        f"🤖 Ваш TKA AI желает вам всего самого наилучшего.\n"
        f"💫 Оставайтесь такими же замечательными!\n\n"
        f"#праздник #поздравление"
    )

    sent_count = 0
    for (user_id,) in users:
        try:
            await bot.send_message(user_id, greeting_text, parse_mode="Markdown")
            sent_count += 1
            await asyncio.sleep(0.05)
        except:
            pass

    print(f"✅ Поздравления отправлены {sent_count} пользователям")

    try:
        await bot.send_message(
            ADMIN_ID,
            f"🎉 **Сегодняшний праздник:** {holiday_name}\n📨 Отправлено {sent_count} пользователям",
            parse_mode="Markdown"
        )
    except:
        pass

# ========== ЗАПУСК ==========
async def on_shutdown():
    await nano.close()

async def main():
    print("📦 Вход в функцию main()")
    await init_db()
    print("🚀 Бот запускается...")

    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_holiday_greeting, "cron", hour=9, minute=0)
    scheduler.start()
    print("⏰ Планировщик праздников запущен (каждый день в 9:00)")

    await dp.start_polling(bot)

if __name__ == "__main__":
    print("🟢 Точка входа")
    try:
        asyncio.run(main())
    finally:
        asyncio.run(on_shutdown())
        