import aiosqlite
from datetime import date, datetime, timedelta

DB_NAME = 'users.db'

async def init_db():
    """Создаёт таблицу пользователей и добавляет недостающие колонки"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                requests_today INTEGER DEFAULT 0,
                last_request_date TEXT,
                is_premium BOOLEAN DEFAULT 0,
                premium_until TEXT,
                permanent_premium BOOLEAN DEFAULT 0,
                joined_date TEXT,
                current_subject TEXT DEFAULT 'mathematics',
                answer_mode TEXT DEFAULT 'full'
            )
        ''')

        # Проверяем наличие всех колонок
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in await cursor.fetchall()]

        if 'permanent_premium' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN permanent_premium BOOLEAN DEFAULT 0")
            print("➕ Добавлена колонка permanent_premium")

        if 'premium_until' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
            print("➕ Добавлена колонка premium_until")

        if 'current_subject' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN current_subject TEXT DEFAULT 'mathematics'")
            print("➕ Добавлена колонка current_subject")

        if 'answer_mode' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN answer_mode TEXT DEFAULT 'full'")
            print("➕ Добавлена колонка answer_mode")

        await db.commit()
    print("✅ База данных готова")

async def set_answer_mode(user_id: int, mode: str):
    """Устанавливает режим ответа: 'full', 'short' или 'cute'"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "UPDATE users SET answer_mode = ? WHERE user_id = ?",
            (mode, user_id)
        )
        await db.commit()

async def get_answer_mode(user_id: int) -> str:
    """Возвращает режим ответа пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT answer_mode FROM users WHERE user_id = ?",
            (user_id,)
        )
        result = await cursor.fetchone()
        return result[0] if result else 'full'

async def get_user(user_id: int):
    """Возвращает пользователя из БД или создаёт нового"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()

        if not user:
            today = str(date.today())
            await db.execute(
                """
                INSERT INTO users
                (user_id, last_request_date, joined_date, requests_today, current_subject, answer_mode)
                VALUES (?, ?, ?, 0, 'mathematics', 'full')
                """,
                (user_id, today, today)
            )
            await db.commit()

            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()

        return user

async def set_user_subject(user_id: int, subject: str):
    """Сохраняет выбранный предмет"""
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_subject = ? WHERE user_id = ?", (subject, user_id))
        await db.commit()

async def get_user_subject(user_id: int) -> str:
    """Возвращает текущий предмет пользователя"""
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT current_subject FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 'mathematics'

async def update_user_requests(user_id: int):
    """Обновляет счётчик запросов"""
    today = str(date.today())
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT requests_today, last_request_date FROM users WHERE user_id = ?",
            (user_id,)
        )
        row = await cursor.fetchone()

        if row:
            requests, last_date = row
            if last_date != today:
                requests = 1
                last_date = today
            else:
                requests += 1

            await db.execute(
                "UPDATE users SET requests_today = ?, last_request_date = ? WHERE user_id = ?",
                (requests, last_date, user_id)
            )
            await db.commit()
            return requests
        return 0

async def check_limit(user_id: int) -> tuple:
    """Проверяет лимит запросов"""
    user = await get_user(user_id)

    # Индексы:
    # 4 — requests_today
    # 6 — is_premium
    # 7 — premium_until
    # 8 — permanent_premium

    if len(user) > 8 and user[8]:
        DAILY_LIMIT = 100
    elif len(user) > 7 and user[6] and user[7] and user[7] >= str(date.today()):
        DAILY_LIMIT = 50
    else:
        DAILY_LIMIT = 15

    requests_today = user[4]

    if requests_today >= DAILY_LIMIT:
        return False, DAILY_LIMIT, requests_today
    return True, DAILY_LIMIT, requests_today

async def activate_premium(user_id: int, days: int = None, permanent: bool = False):
    """Активирует Premium"""
    if days is None and not permanent:
        days = 30

    async with aiosqlite.connect(DB_NAME) as db:
        if permanent:
            await db.execute(
                "UPDATE users SET is_premium = 1, permanent_premium = 1, premium_until = NULL WHERE user_id = ?",
                (user_id,)
            )
        else:
            premium_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
            await db.execute(
                "UPDATE users SET is_premium = 1, permanent_premium = 0, premium_until = ? WHERE user_id = ?",
                (premium_until, user_id)
            )
        await db.commit()
    return await get_user(user_id)