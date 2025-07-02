import aiosqlite
import asyncpg
import os
import json
import aiohttp
from config import DATABASE_PATH, DATABASE_URL

# Database configuration
USE_POSTGRESQL = os.getenv("DATABASE_URL") is not None
USE_REPLIT_DB = os.getenv('REPLIT_DB_URL') is not None or os.path.exists('/tmp/replitdb')

print(f"🔧 Database config: PostgreSQL={USE_POSTGRESQL}, ReplitDB={USE_REPLIT_DB}")

# PostgreSQL connection pool
pg_pool = None

def get_replit_db_url():
    """Get Replit DB URL from environment or file"""
    if os.path.exists('/tmp/replitdb'):
        with open('/tmp/replitdb', 'r') as f:
            return f.read().strip()
    return os.getenv('REPLIT_DB_URL')

class ReplitDB:
    def __init__(self):
        self.url = get_replit_db_url()

    async def set(self, key, value):
        """Set a key-value pair"""
        async with aiohttp.ClientSession() as session:
            async with session.post(self.url, data={key: json.dumps(value)}) as resp:
                return await resp.text()

    async def get(self, key):
        """Get a value by key"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.url}/{key}") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    try:
                        return json.loads(text)
                    except:
                        return text
                return None

    async def delete(self, key):
        """Delete a key"""
        async with aiohttp.ClientSession() as session:
            async with session.delete(f"{self.url}/{key}") as resp:
                return resp.status == 200

    async def list_keys(self, prefix=""):
        """List all keys with optional prefix"""
        async with aiohttp.ClientSession() as session:
            params = {"prefix": prefix} if prefix else {}
            async with session.get(f"{self.url}", params=params) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return text.split('\n') if text else []
                return []

async def get_pg_pool():
    """Получить PostgreSQL connection pool"""
    global pg_pool
    if pg_pool is None and USE_POSTGRESQL:
        try:
            pg_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
            print("✅ PostgreSQL connection pool created")
        except Exception as e:
            print(f"❌ Failed to create PostgreSQL pool: {e}")
    return pg_pool

async def execute_pg_query(query, params=None):
    """Выполнить PostgreSQL запрос"""
    pool = await get_pg_pool()
    if pool:
        async with pool.acquire() as conn:
            return await conn.fetch(query, *(params or []))
    return []

async def execute_pg_update(query, params=None):
    """Выполнить PostgreSQL обновление"""
    pool = await get_pg_pool()
    if pool:
        async with pool.acquire() as conn:
            result = await conn.execute(query, *(params or []))
            return result
    return None

# Initialize database connection
if USE_REPLIT_DB:
    replit_db = ReplitDB()
    print("✅ Using Replit Database for persistent storage")
else:
    replit_db = None
    print("⚠️ Using local SQLite database (data will not persist)")

async def init_db():
    if USE_POSTGRESQL:
        # PostgreSQL initialization
        pool = await get_pg_pool()
        if pool:
            async with pool.acquire() as conn:
                await init_postgresql_tables(conn)
        print("✅ PostgreSQL Database initialized")
        return
    elif USE_REPLIT_DB:
        # For Replit DB, we don't need to create tables
        # Data structure will be managed through keys
        print("✅ Replit Database initialized")
        return

    # Original SQLite initialization for local development
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,

async def init_postgresql_tables(conn):
    """Создаем таблицы PostgreSQL"""
    try:
        # Users table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_subscribed BOOLEAN DEFAULT FALSE,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Giveaways table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS giveaways (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id BIGINT,
                winners_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Giveaway participants table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                id SERIAL PRIMARY KEY,
                giveaway_id INTEGER REFERENCES giveaways(id) ON DELETE CASCADE,
                user_id BIGINT,
                UNIQUE(giveaway_id, user_id)
            )
        ''')

        # Giveaway prizes table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_prizes (
                id SERIAL PRIMARY KEY,
                giveaway_id INTEGER REFERENCES giveaways(id) ON DELETE CASCADE,
                place INTEGER,
                prize TEXT
            )
        ''')

        # Giveaway winners table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_winners (
                id SERIAL PRIMARY KEY,
                giveaway_id INTEGER REFERENCES giveaways(id) ON DELETE CASCADE,
                user_id BIGINT,
                place INTEGER,
                name TEXT,
                username TEXT
            )
        ''')

        # Tournaments table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                winners_count INTEGER DEFAULT 1,
                registration_status TEXT DEFAULT 'open',
                message_id BIGINT
            )
        ''')

        # Tournament participants table
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id SERIAL PRIMARY KEY,
                tournament_id INTEGER REFERENCES tournaments(id) ON DELETE CASCADE,
                user_id BIGINT,
                age INTEGER,
                phone_brand TEXT,
                nickname TEXT,
                game_id TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(tournament_id, user_id)
            )
        ''')

        print("✅ PostgreSQL tables created successfully")
    except Exception as e:
        print(f"❌ Error creating PostgreSQL tables: {e}")


                username TEXT,
                first_name TEXT,
                last_name TEXT,
                is_subscribed BOOLEAN DEFAULT FALSE,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Giveaways table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS giveaways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                end_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id INTEGER,
                winners_count INTEGER DEFAULT 1,
                status TEXT DEFAULT 'active'
            )
        ''')

        # Add missing columns if they don't exist
        try:
            await db.execute('ALTER TABLE giveaways ADD COLUMN winners_count INTEGER DEFAULT 1')
            await db.commit()
        except Exception:
            pass  # Column already exists

        try:
            await db.execute('ALTER TABLE giveaways ADD COLUMN status TEXT DEFAULT "active"')
            await db.commit()
        except Exception:
            pass  # Column already exists

        # Giveaway participants table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER,
                user_id INTEGER,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id),
                UNIQUE(giveaway_id, user_id)
            )
        ''')

        await db.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER,
                place INTEGER,
                prize TEXT,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id)
            )
        ''')

        # Giveaway winners table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_winners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER,
                user_id INTEGER,
                place INTEGER,
                name TEXT,
                username TEXT,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways(id)
            )
        ''')

        # Tournaments table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TEXT,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                winners_count INTEGER DEFAULT 1,
                registration_status TEXT DEFAULT 'open',
                message_id INTEGER
            )
        ''')

        # Add missing columns if they don't exist
        try:
            await db.execute('ALTER TABLE tournaments ADD COLUMN registration_status TEXT DEFAULT "open"')
            await db.commit()
        except Exception:
            pass  # Column already exists

        try:
            await db.execute('ALTER TABLE tournaments ADD COLUMN winners_count INTEGER DEFAULT 1')
            await db.commit()
        except Exception:
            pass  # Column already exists

        # Tournament participants table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tournament_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tournament_id INTEGER,
                user_id INTEGER,
                age INTEGER,
                phone_brand TEXT,
                nickname TEXT,
                game_id TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (tournament_id) REFERENCES tournaments (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(tournament_id, user_id)
            )
        ''')

        await db.commit()

async def add_user(user_id, username=None, first_name=None, last_name=None):
    if USE_REPLIT_DB:
        user_data = {
            'user_id': user_id,
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'is_subscribed': False,
            'registration_date': None
        }
        await replit_db.set(f"user_{user_id}", user_data)
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''
                INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name))
            await db.commit()

async def update_subscription_status(user_id, is_subscribed):
    if USE_REPLIT_DB:
        user_data = await replit_db.get(f"user_{user_id}")
        if not user_data:
            user_data = {'user_id': user_id, 'is_subscribed': False}
        user_data['is_subscribed'] = is_subscribed
        await replit_db.set(f"user_{user_id}", user_data)
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute(
                '''
                UPDATE users SET is_subscribed = ? WHERE user_id = ?
            ''', (is_subscribed, user_id))
            await db.commit()

async def get_user_count():
    if USE_REPLIT_DB:
        keys = await replit_db.list_keys("user_")
        return len(keys)
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute('SELECT COUNT(*) FROM users')
            result = await cursor.fetchone()
            return result[0] if result else 0

async def get_active_users_count():
    if USE_REPLIT_DB:
        keys = await replit_db.list_keys("user_")
        count = 0
        for key in keys:
            user_data = await replit_db.get(key)
            if user_data and user_data.get('is_subscribed'):
                count += 1
        return count
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(
                'SELECT COUNT(*) FROM users WHERE is_subscribed = TRUE')
            result = await cursor.fetchone()
            return result[0] if result else 0