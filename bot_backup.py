import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import init_db, check_limit, update_user_requests, get_user, set_user_subject, get_user_subject
from neural import get_neural_response

# Добавь это после всех импортов
def subject_to_english(russian_subject: str) -> str:
    """Переводит название предмета с русского на английский для БД"""
    subjects = {
        "📐 Математика": "mathematics",
        "⚡ Физика": "physics",
        "🧪 Химия": "chemistry",
        "🧬 Биология": "biology",
        "📖 Русский язык": "russian",
        "🎵 Музыка": "music"
    }
    return subjects.get(russian_subject, "mathematics")

# ========== НАСТРОЙКИ ==========
API_TOKEN = '8690504647:AAF-dfw-q-VcMVrfPm05IjEMVR6aHBQKyAQ'  # ⚠️ ЗАМЕНИ НА СВОЙ!

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# ========== КНОПКИ ==========
def get_main_keyboard():
    """Главная клавиатура с предметами"""
    buttons = [
        [KeyboardButton(text="📐 Математика"), KeyboardButton(text="⚡ Физика")],
        [KeyboardButton(text="🧪 Химия"), KeyboardButton(text="🧬 Биология")],
        [KeyboardButton(text="📖 Русский язык"), KeyboardButton(text="🎵 Музыка")],
        [KeyboardButton(text="📊 Мой лимит"), KeyboardButton(text="💎 Premium")]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

# ========== КОМАНДА СТАРТ ==========
@dp.message(Command("start"))
async def start_command(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    
    await get_user(user_id)
    can_request, limit, used = await check_limit(user_id)
    
    await message.answer(
        f"👋 Привет, {first_name}!\n"
        f"📚 Твой лимит: {used}/{limit} на сегодня\n\n"
        "Выбери предмет и напиши задачу:",
        reply_markup=get_main_keyboard()
    )

# ========== ОБРАБОТЧИКИ КНОПОК ==========
@dp.message(lambda message: message.text == "📐 Математика")
async def math_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "математика")
    await message.answer(
        "📐 Ты выбрал Математику.\n"
        "Теперь все задачи буду решать по математике. Напиши пример или задачу!"
    )

@dp.message(lambda message: message.text == "⚡ Физика")
async def physics_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "физика")
    await message.answer(
        "⚡ Физика. Режим физики включён! Напиши условие задачи — решу с полным оформлением!"
    )

@dp.message(lambda message: message.text == "🧪 Химия")
async def chemistry_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "химия")
    await message.answer(
        "🧪 Химия. Теперь я химик! Жду уравнение или задачу."
    )

@dp.message(lambda message: message.text == "🧬 Биология")
async def bio_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "биология")
    await message.answer(
        "🧬 Биология. Режим биолога включён! О чём расскажем?"
    )

@dp.message(lambda message: message.text == "📖 Русский язык")
async def russian_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "русский язык")
    await message.answer(
        "📖 Русский язык. Теперь я филолог! Присылай слово или предложение — разберём!"
    )

@dp.message(lambda message: message.text == "🎵 Музыка")
async def music_handler(message: types.Message):
    user_id = message.from_user.id
    await set_user_subject(user_id, "музыка")
    await message.answer(
        "🎵 Музыка. Режим музыковеда включён! Спрашивай про композиторов, интервалы, анализ произведений!"
    )

@dp.message(lambda message: message.text == "📊 Мой лимит")
async def limit_handler(message: types.Message):
    user_id = message.from_user.id
    subject = await get_user_subject(user_id)
    can_request, limit, used = await check_limit(user_id)
    await message.answer(
        f"📊 Сегодня использовано: {used}/{limit}\n"
        f"📚 Текущий предмет: {subject}"
    )

@dp.message(lambda message: message.text == "💎 Premium")
async def premium_handler(message: types.Message):
    await message.answer(
        "💎 Premium подписка:\n"
        "• 50 запросов в день\n"
        "• Приоритетная скорость\n"
        "• Доступ ко всем предметам\n\n"
        "🚧 Скоро тут можно будет купить подписку!"
    )

# ========== ОБРАБОТКА ЗАДАЧ ==========
@dp.message()
async def handle_task(message: types.Message):
    user_id = message.from_user.id
    task_text = message.text
    
    # Проверяем лимит
    can_request, limit, used = await check_limit(user_id)
    
    if not can_request:
        await message.answer(
            f"❌ Лимит ({limit}) на сегодня исчерпан!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Получаем текущий предмет пользователя (на английском)
    subject_eng = await get_user_subject(user_id)
    
    # Переводим на русский для красивого отображения
    subject_translate = {
        "mathematics": "Математика",
        "physics": "Физика",
        "chemistry": "Химия",
        "biology": "Биология",
        "russian": "Русский язык",
        "music": "Музыка"
    }
    subject_rus = subject_translate.get(subject_eng, subject_eng)
    
    # Обновляем счётчик запросов
    new_count = await update_user_requests(user_id)
    
    # Отправляем задачу в нейросеть
    thinking_msg = await message.answer("🤔 Думаю...")
    neural_answer = await get_neural_response(subject_eng, task_text)
    
    # Удаляем сообщение "Думаю..." и отправляем ответ
    await thinking_msg.delete()
    await message.answer(
        f"✅ Осталось {limit - new_count} из {limit}\n\n"
        f"{neural_answer}",
        reply_markup=get_main_keyboard()
    )