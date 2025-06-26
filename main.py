
import asyncio
import logging
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, IS_REPLIT, IS_RAILWAY
import config
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
        
        print(f"🔧 Starting server on 0.0.0.0:{port}")
        print(f"🔧 Static files served from: static/")
        
        # Create web app
        app = await create_app(bot_instance)
        print("✅ Web app created successfully")
        
        # Start web server with better error handling
        app_runner = web.AppRunner(app)
        await app_runner.setup()
        
        # Try to start the server
        try:
            site = web.TCPSite(app_runner, '0.0.0.0', port)
            await site.start()
            print(f"✅ Web server started on 0.0.0.0:{port}")
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"⚠️ Port {port} is busy, trying port {port + 1}")
                site = web.TCPSite(app_runner, '0.0.0.0', port + 1)
                await site.start()
                port = port + 1
                print(f"✅ Web server started on 0.0.0.0:{port}")
            else:
                raise
        
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
            
            # Start bot polling in background task with robust error handling
            async def start_bot_polling():
                max_retries = 5
                retry_count = 0
                base_wait = 10
                
                while retry_count < max_retries:
                    try:
                        print(f"🤖 Starting bot polling on Railway (attempt {retry_count + 1}/{max_retries})...")
                        
                        # Clear any existing webhooks with longer wait
                        await bot_instance.delete_webhook(drop_pending_updates=True)
                        await asyncio.sleep(5)
                        
                        # Test bot connectivity
                        me = await bot_instance.get_me()
                        print(f"✅ Bot connected on Railway: @{me.username}")
                        
                        # Start polling
                        await dp_instance.start_polling(bot_instance)
                        print("✅ Bot polling started successfully on Railway")
                        break
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e).lower()
                        
                        if "conflict" in error_msg or "terminated by other getupdates" in error_msg:
                            wait_time = base_wait * (2 ** retry_count)  # Exponential backoff
                            print(f"🔄 Railway bot conflict detected - waiting {wait_time} seconds (attempt {retry_count})")
                            if retry_count < max_retries:
                                await asyncio.sleep(wait_time)
                            else:
                                print("❌ Max retries reached for bot on Railway. Continuing with web server only.")
                                break
                        else:
                            print(f"❌ Railway bot error (attempt {retry_count}): {e}")
                            if retry_count >= max_retries:
                                print("❌ Max retries reached. Railway web server will run without bot.")
                                break
                            await asyncio.sleep(5)
            
            # Create bot task but don't block on it
            bot_task = asyncio.create_task(start_bot_polling())
            
            # Keep the web server running indefinitely
            print("✅ Railway setup complete - web server is running")
            print(f"🌐 Health check available at: https://sasha-production.up.railway.app/health")
            print(f"🌐 Web app available at: https://sasha-production.up.railway.app/")
            
            # Don't wait for bot task, just keep web server alive
            try:
                while True:
                    await asyncio.sleep(60)
                    # Optional: periodically check bot task status
                    if bot_task.done():
                        exception = bot_task.exception()
                        if exception:
                            print(f"🔄 Bot task completed with error: {exception}")
                        else:
                            print("✅ Bot task completed successfully")
            except asyncio.CancelledError:
                print("🛑 Main loop cancelled")
            except Exception as e:
                print(f"❌ Railway main loop error: {e}")
                # Keep running despite errors
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
                max_retries = 3
                retry_count = 0
                
                while retry_count < max_retries:
                    try:
                        print(f"🤖 Starting bot polling (attempt {retry_count + 1}/{max_retries})...")
                        
                        # Clear any existing webhooks and wait longer
                        await bot_instance.delete_webhook(drop_pending_updates=True)
                        await asyncio.sleep(3)  # Увеличиваем задержку
                        
                        # Try to get bot info to check if it's available
                        me = await bot_instance.get_me()
                        print(f"✅ Bot connected: @{me.username}")
                        
                        await dp_instance.start_polling(bot_instance)
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e).lower()
                        print(f"❌ Bot polling error (attempt {retry_count}): {e}")
                        
                        if "conflict" in error_msg or "terminated by other getupdates" in error_msg:
                            wait_time = 10 * retry_count  # Увеличиваем время ожидания с каждой попыткой
                            print(f"🔄 Bot conflict detected - waiting {wait_time} seconds before retry...")
                            await asyncio.sleep(wait_time)
                        elif retry_count >= max_retries:
                            print(f"❌ Max retries reached. Bot polling failed: {e}")
                            break
                        else:
                            await asyncio.sleep(5)
            
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
