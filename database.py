import aiosqlite
from datetime import date, datetime, timedelta

DB_NAME = 'users.db'

async def init_db():
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
                current_subject TEXT DEFAULT 'mathematics'
            )
        ''')
        
        cursor = await db.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in await cursor.fetchall()]
        
        if 'permanent_premium' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN permanent_premium BOOLEAN DEFAULT 0")
        if 'premium_until' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
        if 'current_subject' not in columns:
            await db.execute("ALTER TABLE users ADD COLUMN current_subject TEXT DEFAULT 'mathematics'")
        
        await db.commit()
    print("Database ready")

async def get_user(user_id: int):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = await cursor.fetchone()
        
        if not user:
            today = str(date.today())
            await db.execute(
                "INSERT INTO users (user_id, last_request_date, joined_date, requests_today, current_subject) VALUES (?, ?, ?, 0, 'mathematics')",
                (user_id, today, today)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = await cursor.fetchone()
        
        return user

async def set_user_subject(user_id: int, subject: str):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET current_subject = ? WHERE user_id = ?", (subject, user_id))
        await db.commit()

async def get_user_subject(user_id: int) -> str:
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT current_subject FROM users WHERE user_id = ?", (user_id,))
        result = await cursor.fetchone()
        return result[0] if result else 'mathematics'

async def update_user_requests(user_id: int):
    today = str(date.today())
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT requests_today, last_request_date FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()
        
        if row:
            requests, last_date = row
            if last_date != today:
                requests = 1
                last_date = today
            else:
                requests += 1
            
            await db.execute("UPDATE users SET requests_today = ?, last_request_date = ? WHERE user_id = ?", (requests, last_date, user_id))
            await db.commit()
            return requests
        return 0

async def check_limit(user_id: int) -> tuple:
    user = await get_user(user_id)
    
    if len(user) > 8 and user[8]:
        DAILY_LIMIT = 1000000
    elif len(user) > 7 and user[6] and user[7] and user[7] >= str(date.today()):
        DAILY_LIMIT = 50
    else:
        DAILY_LIMIT = 15
    
    return False if user[4] >= DAILY_LIMIT else True, DAILY_LIMIT, user[4]

async def activate_premium(user_id: int, days: int = None, permanent: bool = False):
    """Активирует Premium для пользователя"""
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
    print(f"Premium activated for user {user_id}")
    return await get_user(user_id)