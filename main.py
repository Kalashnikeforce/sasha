
import asyncio
import logging
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, IS_REPLIT, IS_RAILWAY
from handlers import register_handlers
from database import init_db
from web_app import create_app
from aiohttp import web

# Configure logging based on environment
if IS_RAILWAY:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logging.basicConfig(level=logging.INFO)

# Global variables for cleanup
app_runner = None
bot_instance = None
dp_instance = None

async def cleanup():
    """Cleanup function for graceful shutdown"""
    global app_runner, bot_instance, dp_instance
    
    if dp_instance:
        await dp_instance.stop_polling()
    
    if bot_instance:
        await bot_instance.session.close()
    
    if app_runner:
        await app_runner.cleanup()

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"Received signal {signum}, shutting down gracefully...")
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup())

async def main():
    global app_runner, bot_instance, dp_instance
    
    try:
        # Initialize database
        await init_db()
        print("Database initialized successfully")
        
        # Initialize bot and dispatcher
        bot_instance = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp_instance = Dispatcher(storage=storage)
        
        # Register handlers
        register_handlers(dp_instance, bot_instance)
        print("Bot handlers registered successfully")
        
        # Determine port based on environment
        if IS_RAILWAY:
            port = int(os.getenv("PORT", 8080))
        else:
            port = 5000
        
        # Create web app
        app = await create_app(bot_instance)
        print("Web app created successfully")
        
        # Start web server
        app_runner = web.AppRunner(app)
        await app_runner.setup()
        site = web.TCPSite(app_runner, '0.0.0.0', port)
        await site.start()
        print(f"Web server started on 0.0.0.0:{port}")
        
        environment = "Railway (Production)" if IS_RAILWAY else "Replit (Development)" if IS_REPLIT else "Local"
        print(f"Bot and web app started on port {port}! Environment: {environment}")
        print(f"Web app available at: http://0.0.0.0:{port}")
        
        if IS_RAILWAY:
            print(f"Railway deployment URL: https://sasha-production.up.railway.app")
            print(f"Listening on 0.0.0.0:{port}")
            print("Railway environment variables:", {
                "PORT": os.getenv("PORT"),
                "RAILWAY_ENVIRONMENT": os.getenv("RAILWAY_ENVIRONMENT"),
                "BOT_TOKEN": "***" if BOT_TOKEN else "NOT_SET"
            })
            
            # For Railway, we need to keep both web server and bot running
            # Create tasks for both
            polling_task = asyncio.create_task(dp_instance.start_polling(bot_instance))
            
            # Keep running indefinitely on Railway
            try:
                await polling_task
            except Exception as e:
                print(f"Polling error on Railway: {e}")
                # On Railway, if polling fails, still keep web server running
                while True:
                    await asyncio.sleep(60)  # Keep alive
        else:
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Start polling (this will run indefinitely)
            await dp_instance.start_polling(bot_instance)
            
    except Exception as e:
        print(f"Startup error: {e}")
        if IS_RAILWAY:
            # On Railway, still try to keep web server running even if bot fails
            print("Keeping web server running despite bot error...")
            while True:
                await asyncio.sleep(60)
        else:
            raise
    finally:
        if not IS_RAILWAY:
            await cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Application stopped")
    except Exception as e:
        print(f"Fatal error: {e}")
