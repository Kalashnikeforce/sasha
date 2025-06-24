
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from handlers import register_handlers
from database import init_db
from web_app import create_app
import threading
from aiohttp import web

logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize database
    await init_db()
    
    # Initialize bot and dispatcher
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Register handlers
    register_handlers(dp, bot)
    
    # Start web app in separate thread
    app = await create_app(bot)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()
    
    print("Bot and web app started!")
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
