
import aiosqlite
from config import DATABASE_PATH
import asyncio

import aiosqlite
from config import DATABASE_PATH

async def init_db():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Users table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
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
                message_id INTEGER
            )
        ''')
        
        # Giveaway participants table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                giveaway_id INTEGER,
                user_id INTEGER,
                participation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (giveaway_id) REFERENCES giveaways (id),
                FOREIGN KEY (user_id) REFERENCES users (user_id),
                UNIQUE(giveaway_id, user_id)
            )
        ''')
        
        # Tournaments table
        await db.execute('''
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TIMESTAMP,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
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

async def add_user(user_id, username, first_name, last_name):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        await db.commit()
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                start_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                message_id INTEGER
            )
        ''')
        
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
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO users (user_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        await db.commit()

async def update_subscription_status(user_id, is_subscribed):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE users SET is_subscribed = ? WHERE user_id = ?
        ''', (is_subscribed, user_id))
        await db.commit()

async def get_user_count():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        result = await cursor.fetchone()
        return result[0] if result else 0

async def get_active_users_count():
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM users WHERE is_subscribed = TRUE')
        result = await cursor.fetchone()
        return result[0] if result else 0
