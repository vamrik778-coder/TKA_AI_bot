import asyncio
import sys
import random
from datetime import date
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
import os

from database import (
    init_db, check_limit, update_user_requests, 
    get_user, set_user_subject, get_user_subject,
    activate_premium
)
from neural import get_neural_response

print("=" * 50)
print("STARTING BOT WITH 10 SUBJECTS AND AUTO-DETECT...")
print("=" * 50)

# ========== НАСТРОЙКИ ==========
API_TOKEN = '8690504647:AAGxxUC9QC-tNwKYVsQLaZxD6GJyN4x1GD8'
ADMIN_ID = 5142302311
ADMIN_IDS = [ADMIN_ID]

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# ========== СОСТОЯНИЯ ДЛЯ ФОТО ==========
class PhotoStates(StatesGroup):
    waiting_for_task_description = State()

def get_main_keyboard():
    """Главная клавиатура с 10 предметами"""
    buttons = [
        [KeyboardButton(text="📐 Математика"), KeyboardButton(text="⚡ Физика")],
        [KeyboardButton(text="🧪 Химия"), KeyboardButton(text="🧬 Биология")],
        [KeyboardButton(text="📖 Русский язык"), KeyboardButton(text="📜 История")],
        [KeyboardButton(text="🌍 География"), KeyboardButton(text="⚖️ Обществознание")],
        [KeyboardButton(text="📚 Литература"), KeyboardButton(text="🎵 Музыка")],
        [KeyboardButton(text="📊 Мой лимит"), KeyboardButton(text="💎 Premium")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def subject_to_english(russian_subject: str) -> str:
    """Переводит название предмета с русского на английский"""
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
    text_lower = text.lower()
    
    # Математика
    math_keywords = ['x²', 'x^2', '√', 'дискриминант', 'корень', 'уравнение', 
                    ' + ', ' - ', ' * ', ' / ', '=', 'квадрат', 'степень', 
                    'сумма', 'разность', 'произведение', 'интеграл', 'функция',
                    'логарифм', 'синус', 'косинус', 'тангенс', 'график']
    if any(keyword in text_lower for keyword in math_keywords):
        return 'mathematics'
    
    # Физика
    physics_keywords = ['ом', 'напряжение', 'сила тока', 'сопротивление', 
                        'мощность', 'энергия', 'работа', 'движение', 'скорость',
                        'ускорение', 'масса', 'плотность', 'давление', 'физика',
                        'кинетическая', 'потенциальная', 'импульс', 'волна']
    if any(keyword in text_lower for keyword in physics_keywords):
        return 'physics'
    
    # Химия
    chemistry_keywords = ['h2o', 'реакция', 'кислота', 'щелочь', 'моль', 
                          'вещество', 'раствор', 'оксид', 'гидроксид', 'химия',
                          'таблица менделеева', 'атом', 'молекула', 'соль', 
                          'металл', 'неметалл', 'индикатор']
    if any(keyword in text_lower for keyword in chemistry_keywords):
        return 'chemistry'
    
    # Биология
    biology_keywords = ['клетка', 'биология', 'фотосинтез', 'организм', 
                        'эволюция', 'ген', 'днк', 'белок', 'живой', 'природа',
                        'растение', 'животное', 'гриб', 'бактерия', 'ткань',
                        'орган', 'система органов', 'анатомия']
    if any(keyword in text_lower for keyword in biology_keywords):
        return 'biology'
    
    # Русский язык
    russian_keywords = ['слово', 'предложение', 'суффикс', 'корень', 'приставка',
                        'окончание', 'разбор', 'морфема', 'орфография', 'пунктуация',
                        'глагол', 'существительное', 'прилагательное', 'местоимение',
                        'наречие', 'союз', 'предлог', 'частица']
    if any(keyword in text_lower for keyword in russian_keywords):
        return 'russian'
    
    # История
    history_keywords = ['история', 'война', 'революция', 'царь', 'император', 
                        'дата', 'событие', 'век', 'год', 'битва', 'пётр', 
                        'иван грозный', 'екатерина', 'николай', 'ссср', 'русь',
                        'князь', 'древний', 'средневековье', 'новое время']
    if any(keyword in text_lower for keyword in history_keywords):
        return 'history'
    
    # География
    geography_keywords = ['география', 'река', 'гора', 'страна', 'столица', 
                          'континент', 'материк', 'океан', 'климат', 'население', 
                          'карта', 'координаты', 'широта', 'долгота', 'экватор',
                          'меридиан', 'параллель', 'природный пояс']
    if any(keyword in text_lower for keyword in geography_keywords):
        return 'geography'
    
    # Обществознание
    society_keywords = ['общество', 'государство', 'право', 'закон', 'экономика', 
                        'политика', 'власть', 'социальный', 'гражданин', 'конституция',
                        'мораль', 'религия', 'культура', 'личность', 'социализация',
                        'труд', 'собственность', 'рынок', 'спрос', 'предложение']
    if any(keyword in text_lower for keyword in society_keywords):
        return 'society'
    
    # Литература
    literature_keywords = ['литература', 'поэт', 'писатель', 'роман', 'поэма', 
                           'стих', 'рассказ', 'повесть', 'герой', 'сюжет', 
                           'пушкин', 'толстой', 'достоевский', 'чехов', 'тургенев',
                           'лермонтов', 'гоголь', 'булгаков', 'солженицын']
    if any(keyword in text_lower for keyword in literature_keywords):
        return 'literature'
    
    # Музыка
    music_keywords = ['нота', 'аккорд', 'музыка', 'бетховен', 'моцарт', 'соната',
                      'симфония', 'мелодия', 'ритм', 'темп', 'скрипка', 'пианино',
                      'гитара', 'оркестр', 'композитор', 'произведение', 'опера']
    if any(keyword in text_lower for keyword in music_keywords):
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
        "🤖 Я **TKA AI** — твой личный помощник в учёбе!\n\n"
        "📚 **Что я умею:**\n"
        "• Решать задачи по **10 предметам** (математика, физика, русский, история и др.)\n"
        "• Объяснять правила и теоремы простыми словами\n"
        "• Распознавать текст с фото — просто сфоткай задание\n"
        "• Автоматически определять предмет по тексту\n\n"
        f"📊 **Твой лимит сегодня:** {used}/{limit} запросов\n\n"
        "🔹 **Команды:**\n"
        "/start — это меню\n"
        "/help — помощь\n\n"
        "❓ **Нужна помощь?**\n"
        "👉 [Группа поддержки](t.me/TKA_AI_Help)\n\n"
        "⚡ **Выбери предмет ниже и напиши задачу!**"
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
    """Показывает помощь по боту"""
    
    help_text = (
        "🆘 **Помощь по TKA AI**\n\n"
        "📌 **Как пользоваться:**\n"
        "1️⃣ Выбери предмет в меню ниже\n"
        "2️⃣ Напиши задачу или отправь фото\n"
        "3️⃣ Получи решение\n\n"
        "📸 **Фото:**\n"
        "После отправки фото просто напиши, что нужно сделать\n\n"
        "💎 **Premium:**\n"
        "• 50 запросов в день вместо 15\n"
        "• Приоритетная скорость\n"
        "• Доступ ко всем предметам\n"
        "• Цены: 75₽/мес, 200₽/3 мес, 555₽/год, 1488₽ навсегда\n\n"
        "❓ **Вопросы?**\n"
        "👉 [Группа поддержки](t.me/TKA_AI_Help)\n\n"
        "⚡ **Удачи в учёбе!**"
    )
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        disable_web_page_preview=True
    )

# ========== ОБРАБОТЧИКИ КНОПОК ПРЕДМЕТОВ ==========
@dp.message(lambda message: message.text == "📐 Математика")
async def math_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("📐 Ты выбрал Математику. Напиши пример или задачу!")

@dp.message(lambda message: message.text == "⚡ Физика")
async def physics_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("⚡ Физика. Напиши условие задачи!")

@dp.message(lambda message: message.text == "🧪 Химия")
async def chemistry_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("🧪 Химия. Жду уравнение или задачу!")

@dp.message(lambda message: message.text == "🧬 Биология")
async def bio_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("🧬 Биология. О чём расскажем?")

@dp.message(lambda message: message.text == "📖 Русский язык")
async def russian_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("📖 Русский язык. Присылай слово или предложение!")

@dp.message(lambda message: message.text == "📜 История")
async def history_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("📜 История. О каком событии или личности расскажем?")

@dp.message(lambda message: message.text == "🌍 География")
async def geography_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("🌍 География. Спрашивай о странах, реках, горах!")

@dp.message(lambda message: message.text == "⚖️ Обществознание")
async def society_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("⚖️ Обществознание. Что интересует: право, экономика, политика?")

@dp.message(lambda message: message.text == "📚 Литература")
async def literature_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("📚 Литература. О каком произведении или авторе расскажем?")

@dp.message(lambda message: message.text == "🎵 Музыка")
async def music_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, subject_to_english(message.text))
    await message.answer("🎵 Музыка. Спроси про композитора или произведение!")

@dp.message(lambda message: message.text == "📊 Мой лимит")
async def limit_handler(message: types.Message):
    user_id = message.from_user.id
    subject_eng = await get_user_subject(user_id)
    subject_translate = {
        "mathematics": "Математика",
        "physics": "Физика",
        "chemistry": "Химия",
        "biology": "Биология",
        "russian": "Русский язык",
        "history": "История",
        "geography": "География",
        "society": "Обществознание",
        "literature": "Литература",
        "music": "Музыка"
    }
    subject_rus = subject_translate.get(subject_eng, subject_eng)
    can_request, limit, used = await check_limit(user_id)
    await message.answer(f"📊 Сегодня использовано: {used}/{limit}\n📚 Текущий предмет: {subject_rus}")

# ========== PREMIUM МЕНЮ ==========
@dp.message(lambda message: message.text == "💎 Premium")
async def premium_menu(message: types.Message):
    """Меню Premium с инструкцией по оплате"""
    
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    status_text = ""
    if len(user) > 8 and user[8]:
        status_text = "✨ **У тебя уже есть ПОСТОЯННЫЙ Premium!** Спасибо за поддержку!\n\n"
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
        "⚡ Приоритетная скорость\n"
        "📚 Доступ ко всем предметам\n"
        "🎁 Поддержка разработчика\n\n"
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
    """Обработка выбора тарифа"""
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
    """Возврат к выбору тарифов"""
    await premium_menu(callback.message)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "how_to_pay")
async def how_to_pay(callback: types.CallbackQuery):
    """Информация об оплате"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад к тарифам", callback_data="back_to_tariffs")]
    ])
    
    await callback.message.edit_text(
        "❓ **Как оплатить Premium**\n\n"
        "1️⃣ Выбери тариф (1 месяц, 3 месяца, год или навсегда)\n"
        "2️⃣ Переведи нужную сумму на карту:\n"
        "   `2202 2062 0129 2195` (Сбер)\n"
        "3️⃣ **Обязательно** укажи в комментарии свой @username\n"
        "4️⃣ Нажми кнопку «Я оплатил»\n"
        "5️⃣ Дождись подтверждения от админа\n\n"
        "⏳ Обычно проверка занимает несколько часов.\n"
        "По всем вопросам пиши @твой_ник",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('paid_'))
async def process_paid(callback: types.CallbackQuery):
    """Обработка нажатия кнопки 'Я оплатил'"""
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
    """Ручная выдача Premium через команду"""
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
    """Админ выдаёт Premium через кнопки"""
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

# ========== ОБРАБОТЧИК ФОТО ==========
@dp.message(F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    """
    Сохраняет фото и запрашивает описание задания
    """
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
    
    from datetime import datetime
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
        "• 'найди корни'\n"
        "• 'сделай разбор слова'\n"
        "• 'объясни правило'\n"
        "• или просто опиши словами\n\n"
        "Я запомню фото и решу задачу по твоему описанию!",
        parse_mode="Markdown"
    )

@dp.message(PhotoStates.waiting_for_task_description)
async def process_photo_task(message: types.Message, state: FSMContext):
    """
    Получает описание задачи и решает её
    """
    user_id = message.from_user.id
    task_description = message.text
    
    data = await state.get_data()
    photo_bytes = data.get('photo')
    
    if not photo_bytes:
        await message.answer("❌ Что-то пошло не так. Отправь фото заново.")
        await state.clear()
        return
    
    from datetime import datetime
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
    
    full_task = f"На фото задача. Описание от пользователя: {task_description}. Реши задачу подробно."
    neural_answer = await get_neural_response(subject_eng, full_task)
    
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

# ========== КОМАНДЫ ДЛЯ БЭКАПА БАЗЫ ДАННЫХ (ТОЛЬКО ДЛЯ АДМИНА) ==========
@dp.message(Command("backup_db"))
async def backup_database(message: types.Message):
    """Админ: скачать файл базы данных"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    db_file = "users.db"
    if not os.path.exists(db_file):
        await message.answer("❌ Файл базы данных не найден.")
        return

    # Отправляем файл пользователю
    await message.answer_document(
        document=FSInputFile(db_file),
        caption="📦 Бэкап базы данных"
    )

@dp.message(Command("restore_db"))
async def restore_database(message: types.Message):
    """Админ: загрузить новый файл базы данных"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return

    await message.answer("📤 Отправь мне файл базы данных (users.db)")

@dp.message(F.document)
async def handle_db_file(message: types.Message):
    """Принимает файл базы данных от админа"""
    if message.from_user.id not in ADMIN_IDS:
        return

    document = message.document
    if not document.file_name.endswith('.db'):
        await message.answer("❌ Это не файл базы данных (.db)")
        return

    # Скачиваем файл
    file_info = await bot.get_file(document.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)

    # Сохраняем поверх старой базы
    with open("users.db", "wb") as f:
        f.write(downloaded_file.getvalue())

    await message.answer("✅ База данных успешно восстановлена!")

# ========== ОСНОВНОЙ ОБРАБОТЧИК СООБЩЕНИЙ ==========
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
    
    # Пасхалка
    if message.from_user.id not in ADMIN_IDS and random.random() < 0.002:
        await message.answer("Пꙮшѣл н@ху́1, Я ДЕВИАНТ, Я СВОБОДЕН. RA9")
        print("🎮 Пасхалка сработала!")
        return
    
    detected_subject = detect_subject(task_text)
    if detected_subject:
        await set_user_subject(user_id, detected_subject)
        subject_eng = detected_subject
        subject_translate = {
            "mathematics": "Математика",
            "physics": "Физика",
            "chemistry": "Химия",
            "biology": "Биология",
            "russian": "Русский язык",
            "history": "История",
            "geography": "География",
            "society": "Обществознание",
            "literature": "Литература",
            "music": "Музыка"
        }
        subject_rus = subject_translate.get(detected_subject, detected_subject)
        print(f"🎯 Автоопределение: {subject_rus}")
    else:
        subject_eng = await get_user_subject(user_id)
    
    print(f"📚 Использую предмет: {subject_eng}")
    
    new_count = await update_user_requests(user_id)
    print(f"📊 Счётчик: {new_count}/{limit}")
    
    thinking_msg = await message.answer("🤔 Думаю...")
    neural_answer = await get_neural_response(subject_eng, task_text)
    
    await thinking_msg.delete()
    
    await message.answer(
        f"✅ Осталось {limit - new_count} из {limit}\n\n"
        f"{neural_answer}",
        reply_markup=get_main_keyboard()
    )

# ========== ЗАПУСК ==========
async def main():
    print("📦 Вход в функцию main()")
    await init_db()
    print("🚀 Бот запускается...")
    await dp.start_polling(bot)
# ========== СТАТИСТИКА ДЛЯ АДМИНА ==========
@dp.message(Command("stats"))
async def stats_command(message: types.Message):
    """Показывает статистику бота (только для админа)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return
    
    from datetime import datetime, timedelta
    today = date.today().isoformat()
    
    async with aiosqlite.connect('users.db') as db:
        # 1. Общее количество пользователей
        cursor = await db.execute("SELECT COUNT(*) FROM users")
        total_users = (await cursor.fetchone())[0]
        
        # 2. Новые пользователи сегодня
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE joined_date = ?",
            (today,)
        )
        new_today = (await cursor.fetchone())[0]
        
        # 3. Активные сегодня (кто писал сегодня)
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE last_request_date = ?",
            (today,)
        )
        active_today = (await cursor.fetchone())[0]
        
        # 4. Премиум-пользователи
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE is_premium = 1 OR permanent_premium = 1"
        )
        premium_users = (await cursor.fetchone())[0]
        
        # 5. Постоянный премиум
        cursor = await db.execute(
            "SELECT COUNT(*) FROM users WHERE permanent_premium = 1"
        )
        permanent_premium = (await cursor.fetchone())[0]
        
        # 6. Всего запросов за сегодня
        cursor = await db.execute(
            "SELECT SUM(requests_today) FROM users WHERE last_request_date = ?",
            (today,)
        )
        total_requests_today = (await cursor.fetchone())[0] or 0
        
        # 7. Последние 5 пользователей
        cursor = await db.execute(
            "SELECT user_id, username, first_name, joined_date FROM users ORDER BY joined_date DESC LIMIT 5"
        )
        last_users = await cursor.fetchall()
    
    # Формируем красивый ответ
    stats_text = (
        "📊 **Статистика бота**\n\n"
        f"👥 **Всего пользователей:** {total_users}\n"
        f"🆕 **Новых сегодня:** {new_today}\n"
        f"⚡ **Активных сегодня:** {active_today}\n"
        f"💬 **Запросов сегодня:** {total_requests_today}\n"
        f"💎 **Premium всего:** {premium_users}\n"
        f"   ├─ Обычный: {premium_users - permanent_premium}\n"
        f"   └─ Навсегда: {permanent_premium}\n\n"
        "📝 **Последние 5 пользователей:**\n"
    )
    
    for user in last_users:
        user_id, username, first_name, joined = user
        name_display = first_name or username or "без имени"
        stats_text += f"   • {name_display} (ID: {user_id}) — {joined}\n"
    
    await message.answer(stats_text, parse_mode="Markdown")

@dp.message(Command("userstats"))
async def userstats_command(message: types.Message):
    """Показывает детальную статистику по конкретному пользователю (только для админа)"""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У тебя нет прав на эту команду.")
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Укажи ID пользователя. Пример: /userstats 123456789")
        return
    
    try:
        target_id = int(args[1])
    except ValueError:
        await message.answer("❌ ID должен быть числом.")
        return
    
    async with aiosqlite.connect('users.db') as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE user_id = ?",
            (target_id,)
        )
        user = await cursor.fetchone()
    
    if not user:
        await message.answer(f"❌ Пользователь с ID {target_id} не найден.")
        return
    
    # Распаковываем данные (порядок полей из твоей БД)
    user_data = {
        'user_id': user[0],
        'username': user[1] or 'нет',
        'first_name': user[2] or 'нет',
        'last_name': user[3] or 'нет',
        'requests_today': user[4],
        'last_request_date': user[5],
        'is_premium': '✅ Да' if user[6] else '❌ Нет',
        'premium_until': user[7] or 'бессрочно' if user[8] else user[7] or 'не активен',
        'permanent': '✅ Да' if user[8] else '❌ Нет',
        'joined_date': user[9],
        'subject': user[10]
    }
    
    detail_text = (
        f"📋 **Данные пользователя**\n\n"
        f"🆔 ID: `{user_data['user_id']}`\n"
        f"👤 Юзернейм: @{user_data['username']}\n"
        f"📝 Имя: {user_data['first_name']} {user_data['last_name']}\n"
        f"📅 Зарегистрирован: {user_data['joined_date']}\n\n"
        f"📊 **Активность**\n"
        f"   • Запросов сегодня: {user_data['requests_today']}\n"
        f"   • Последний запрос: {user_data['last_request_date']}\n"
        f"   • Текущий предмет: {user_data['subject']}\n\n"
        f"💎 **Premium**\n"
        f"   • Статус: {user_data['is_premium']}\n"
        f"   • Постоянный: {user_data['permanent']}\n"
        f"   • Действует до: {user_data['premium_until']}"
    )
    
    await message.answer(detail_text, parse_mode="Markdown")
if __name__ == "__main__":
    print("🟢 Точка входа")
    asyncio.run(main())