import asyncpg
from config import DATABASE_PUBLIC_URL, USE_POSTGRESQL

async def init_db():
    if USE_POSTGRESQL:
        # PostgreSQL initialization
        print("🐘 Initializing PostgreSQL database...")
        try:
            conn = await asyncpg.connect(DATABASE_PUBLIC_URL)

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
                    giveaway_id INTEGER REFERENCES giveaways(id),
                    user_id BIGINT,
                    UNIQUE(giveaway_id, user_id)
                )
            ''')

            # Giveaway prizes table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS giveaway_prizes (
                    id SERIAL PRIMARY KEY,
                    giveaway_id INTEGER REFERENCES giveaways(id),
                    place INTEGER,
                    prize TEXT
                )
            ''')

            # Giveaway winners table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS giveaway_winners (
                    id SERIAL PRIMARY KEY,
                    giveaway_id INTEGER REFERENCES giveaways(id),
                    user_id BIGINT REFERENCES users(user_id),
                    place INTEGER,
                    name TEXT,
                    username TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    tournament_id INTEGER REFERENCES tournaments(id),
                    user_id BIGINT REFERENCES users(user_id),
                    age INTEGER,
                    phone_brand TEXT,
                    nickname TEXT,
                    game_id TEXT,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(tournament_id, user_id)
                )
            ''')

            await conn.close()
            print("✅ PostgreSQL database initialized successfully")

        except Exception as e:
            print(f"❌ PostgreSQL initialization error: {e}")
            raise
    else:
        raise Exception("❌ PostgreSQL not configured! Please set DATABASE_PUBLIC_URL in secrets.")

async def add_user(user_id, username=None, first_name=None, last_name=None):
    if USE_POSTGRESQL:
        try:
            conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
            await conn.execute(
                '''
                INSERT INTO users (user_id, username, first_name, last_name)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE SET
                    username = $2,
                    first_name = $3,
                    last_name = $4
                ''', user_id, username, first_name, last_name)
            await conn.close()
        except Exception as e:
            print(f"PostgreSQL add_user error: {e}")
    else:
        raise Exception("❌ PostgreSQL not configured")

async def update_subscription_status(user_id, is_subscribed):
    if USE_POSTGRESQL:
        try:
            conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
            await conn.execute(
                '''
                UPDATE users SET is_subscribed = $1 WHERE user_id = $2
                ''', is_subscribed, user_id)
            await conn.close()
        except Exception as e:
            print(f"PostgreSQL update_subscription error: {e}")
    else:
        raise Exception("❌ PostgreSQL not configured")

async def get_user_count():
    if USE_POSTGRESQL:
        try:
            conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
            result = await conn.fetchval('SELECT COUNT(*) FROM users')
            await conn.close()
            return result if result else 0
        except Exception as e:
            print(f"PostgreSQL get_user_count error: {e}")
            return 0
    else:
        raise Exception("❌ PostgreSQL not configured")

async def get_active_users_count():
    if USE_POSTGRESQL:
        try:
            conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
            result = await conn.fetchval('SELECT COUNT(*) FROM users WHERE is_subscribed = TRUE')
            await conn.close()
            return result if result else 0
        except Exception as e:
            print(f"PostgreSQL get_active_users_count error: {e}")
            return 0
    else:
        raise Exception("❌ PostgreSQL not configured")