
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
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(cleanup())
    except Exception as e:
        print(f"Error in signal handler: {e}")

async def main():
    global app_runner, bot_instance, dp_instance
    
    try:
        print("Starting application initialization...")
        
        # Initialize database
        await init_db()
        print("✅ Database initialized successfully")
        
        # Initialize bot and dispatcher
        bot_instance = Bot(token=BOT_TOKEN)
        storage = MemoryStorage()
        dp_instance = Dispatcher(storage=storage)
        
        # Register handlers
        register_handlers(dp_instance, bot_instance)
        print("✅ Bot handlers registered successfully")
        
        # Determine port based on environment
        if IS_RAILWAY:
            port = int(os.getenv("PORT", 10000))
            print(f"🔧 Railway PORT detected: {port}")
        else:
            port = 5000
            print(f"🔧 Using Replit port: {port}")
        
        # Create web app
        app = await create_app(bot_instance)
        print("✅ Web app created successfully")
        
        # Start web server
        app_runner = web.AppRunner(app)
        await app_runner.setup()
        site = web.TCPSite(app_runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Web server started on 0.0.0.0:{port}")
        
        environment = "Railway (Production)" if IS_RAILWAY else "Replit (Development)" if IS_REPLIT else "Local"
        print(f"🚀 Bot and web app started on port {port}! Environment: {environment}")
        
        if IS_RAILWAY:
            print(f"🌐 Railway URL: https://sasha-production.up.railway.app")
            print(f"🔧 Environment vars: PORT={os.getenv('PORT')}, RAILWAY_ENV={os.getenv('RAILWAY_ENVIRONMENT')}")
            print(f"🔧 BOT_TOKEN configured: {'Yes' if BOT_TOKEN else 'No'}")
            
            # Set up proper signal handlers for Railway
            def railway_signal_handler(signum, frame):
                print(f"🛑 Received signal {signum} on Railway, graceful shutdown...")
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(cleanup())
                except Exception as e:
                    print(f"Error during cleanup: {e}")
            
            signal.signal(signal.SIGINT, railway_signal_handler)
            signal.signal(signal.SIGTERM, railway_signal_handler)
            
            # Start bot polling in background task
            async def start_bot_polling():
                try:
                    print("🤖 Starting bot polling...")
                    await dp_instance.start_polling(bot_instance)
                except Exception as e:
                    print(f"❌ Bot polling error: {e}")
            
            # Create bot task but don't await it immediately
            bot_task = asyncio.create_task(start_bot_polling())
            
            # Keep the web server running indefinitely
            print("✅ Railway setup complete - keeping web server alive...")
            print(f"🌐 Health check available at: https://sasha-production.up.railway.app/health")
            try:
                # Wait for bot task or run forever
                await bot_task
            except asyncio.CancelledError:
                print("🛑 Bot task cancelled")
            except Exception as e:
                print(f"❌ Bot task error: {e}")
                # Keep web server running even if bot fails
                print("🔄 Keeping web server running despite bot error...")
                while True:
                    await asyncio.sleep(60)
                    
        else:
            # Replit/Local setup
            print(f"🌐 Local URL: http://0.0.0.0:{port}")
            
            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # Start bot polling in background task for Replit
            async def start_bot_polling():
                try:
                    print("🤖 Starting bot polling...")
                    await dp_instance.start_polling(bot_instance)
                except Exception as e:
                    print(f"❌ Bot polling error: {e}")
            
            # Create bot task
            bot_task = asyncio.create_task(start_bot_polling())
            
            # Keep the web server running
            print("✅ Replit setup complete - keeping web server alive...")
            try:
                await bot_task
            except asyncio.CancelledError:
                print("🛑 Bot task cancelled")
            except Exception as e:
                print(f"❌ Bot task error: {e}")
                # Keep web server running even if bot fails
                print("🔄 Keeping web server running despite bot error...")
                while True:
                    await asyncio.sleep(60)
            
    except Exception as e:
        print(f"💥 Startup error: {e}")
        import traceback
        traceback.print_exc()
        
        if IS_RAILWAY:
            # On Railway, try to keep web server running
            print("🆘 Attempting to keep web server running...")
            try:
                while True:
                    await asyncio.sleep(60)
            except KeyboardInterrupt:
                print("🛑 Forced shutdown")
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
