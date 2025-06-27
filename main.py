import asyncio
import logging
import os
import signal
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, DATABASE_PATH, ADMIN_IDS, MODE, CHANNEL_ID, WEB_APP_URL, IS_REPLIT, IS_RAILWAY
import aiosqlite
from aiogram import F
import config
from handlers import register_handlers
from database import init_db
from web_app import create_app
from aiohttp import web

# Configure logging based on environment
if IS_RAILWAY:
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    # Disable aiohttp access logs for cleaner output
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
else:
    logging.basicConfig(level=logging.WARNING)
    # Disable aiohttp access logs for cleaner output  
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)

# Global variables for cleanup
app_runner = None
bot_instance = None
dp_instance = None

async def cleanup():
    """Cleanup function for graceful shutdown"""
    global app_runner, bot_instance, dp_instance

    print("🧹 Starting cleanup...")

    try:
        if dp_instance:
            print("🛑 Stopping bot polling...")
            await dp_instance.stop_polling()
    except Exception as e:
        print(f"⚠️ Error stopping polling: {e}")

    try:
        if bot_instance:
            print("🔌 Closing bot session...")
            await bot_instance.session.close()
    except Exception as e:
        print(f"⚠️ Error closing bot session: {e}")

    try:
        if app_runner:
            print("🌐 Cleaning up web server...")
            await app_runner.cleanup()
    except Exception as e:
        print(f"⚠️ Error cleaning up web server: {e}")

    print("✅ Cleanup completed")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"📡 Received signal {signum}, initiating graceful shutdown...")
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            print("🔄 Creating cleanup task...")
            task = loop.create_task(cleanup())
            # Give cleanup some time to complete
            loop.run_until_complete(asyncio.wait_for(task, timeout=10))
    except Exception as e:
        print(f"❌ Error in signal handler: {e}")
    finally:
        print("🛑 Exiting...")
        os._exit(0)

async def main():
    global app_runner, bot_instance, dp_instance
    from aiogram import Bot, Dispatcher
    from aiogram.client.default import DefaultBotProperties
    from aiogram.enums import ParseMode
    from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram import F
    import asyncio
    import aiohttp
    from aiohttp import web
    import signal
    import sys
    import os
    import aiosqlite
    from config import BOT_TOKEN, DATABASE_PATH, ADMIN_IDS, MODE, CHANNEL_ID, WEB_APP_URL
    from database import init_db
    from handlers import register_handlers
    from web_app import create_app

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

        # Register callback handler for giveaway participation
        @dp_instance.callback_query(F.data.startswith("giveaway_participate_"))
        async def handle_giveaway_participation(callback: CallbackQuery):
            try:
                giveaway_id = int(callback.data.split("_")[-1])
                user_id = callback.from_user.id

                async with aiosqlite.connect(DATABASE_PATH) as db:
                    # Check if user already participated
                    cursor = await db.execute('''
                        SELECT id FROM giveaway_participants WHERE giveaway_id = ? AND user_id = ?
                    ''', (giveaway_id, user_id))
                    existing = await cursor.fetchone()

                    if existing:
                        await callback.answer("❌ Вы уже участвуете в этом розыгрыше!", show_alert=True)
                        return

                    # Add participant
                    await db.execute('''
                        INSERT INTO giveaway_participants (giveaway_id, user_id)
                        VALUES (?, ?)
                    ''', (giveaway_id, user_id))
                    await db.commit()

                    # Get updated participant count
                    cursor = await db.execute('''
                        SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id = ?
                    ''', (giveaway_id,))
                    count = await cursor.fetchone()
                    participant_count = count[0] if count else 0

                    # Update button with new participant count
                    new_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"🎮 Участвовать ({participant_count})", callback_data=f"giveaway_participate_{giveaway_id}")]
                    ])

                    try:
                        await callback.message.edit_reply_markup(reply_markup=new_keyboard)
                    except Exception as edit_error:
                        print(f"Error updating button: {edit_error}")

                    await callback.answer("✅ Вы успешно зарегистрированы в розыгрыше!", show_alert=True)

            except Exception as e:
                print(f"Error in giveaway participation: {e}")
                await callback.answer("❌ Произошла ошибка при регистрации", show_alert=True)

        # Tournament registration is now handled via /start command with deep link

        print("✅ Bot handlers registered successfully")

        # Determine port based on environment
        if IS_RAILWAY:
            port = int(os.getenv("PORT", 10000))
            print(f"🔧 Railway PORT: {port}")
        else:
            port = 5000
            print(f"🔧 Using default port: {port}")

        # Create web app first (faster startup for Railway)
        print("⚡ Creating web app for fast startup...")
        app = await create_app(bot_instance)
        print("✅ Web app created")

        # Start web server immediately for Railway health check
        print("🚀 Starting web server...")
        app_runner = web.AppRunner(app)
        await app_runner.setup()

        site = web.TCPSite(app_runner, '0.0.0.0', port)
        await site.start()
        print(f"✅ Web server started on 0.0.0.0:{port}")

        environment = "Railway (Production)" if IS_RAILWAY else "Replit (Development)" if IS_REPLIT else "Local"
        print(f"🚀 Service ready on port {port}! Environment: {environment}")

        if IS_RAILWAY:
            print(f"🌐 Railway URL: https://sasha-production.up.railway.app")
            print(f"🏥 Health check endpoint: /health")
            print("🚀 PRODUCTION MODE: Railway - Full functionality")
            print("✅ Bot polling ENABLED (Production setup)")

            # Start bot polling in background task for Railway too
            async def start_bot_polling():
                max_retries = 3
                retry_count = 0

                # Добавляем дополнительную задержку для предотвращения конфликтов
                print("⏳ Waiting 5 seconds before starting bot to avoid conflicts...")
                await asyncio.sleep(5)

                while retry_count < max_retries:
                    try:
                        print(f"🤖 Starting bot polling (attempt {retry_count + 1}/{max_retries})...")

                        # Принудительно очищаем все webhook и ждем
                        try:
                            await bot_instance.delete_webhook(drop_pending_updates=True)
                            await asyncio.sleep(3)
                            print("✅ Webhooks cleared")
                        except Exception as webhook_error:
                            print(f"⚠️ Webhook clearing error: {webhook_error}")

                        # Проверяем доступность бота
                        me = await bot_instance.get_me()
                        print(f"✅ Bot connected: @{me.username}")

                        # Дополнительная задержка перед началом polling
                        await asyncio.sleep(2)

                        # Start polling with proper error handling
                        await dp_instance.start_polling(bot_instance, handle_signals=False)
                        break  # Success, exit retry loop

                    except asyncio.CancelledError:
                        print("🛑 Bot polling cancelled")
                        break
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e).lower()
                        print(f"❌ Bot polling error (attempt {retry_count}): {e}")

                        if "conflict" in error_msg or "terminated by other getupdates" in error_msg:
                            wait_time = 20 + (10 * retry_count)  # Увеличиваем время ожидания
                            print(f"🔄 Bot conflict detected - waiting {wait_time} seconds...")
                            if retry_count < max_retries:
                                await asyncio.sleep(wait_time)
                            else:
                                print("❌ Max retries reached. Bot conflict persists.")
                                print("🛑 Web app will continue working without bot polling.")
                                break
                        elif retry_count >= max_retries:
                            print(f"❌ Max retries reached. Bot polling failed: {e}")
                            break
                        else:
                            await asyncio.sleep(5)

            # Create bot task but don't wait for it
            bot_task = asyncio.create_task(start_bot_polling())

            # Keep the web server running indefinitely
            print("✅ Railway setup complete - keeping web server alive...")
            try:
                while True:
                    await asyncio.sleep(30)
                    # Check if bot task is still running
                    if bot_task.done():
                        exception = bot_task.exception()
                        if exception:
                            print(f"🔄 Bot task finished with error: {exception}")
                        else:
                            print("✅ Bot task completed")
                        # Don't restart bot task to avoid conflicts
            except asyncio.CancelledError:
                print("🛑 Main loop cancelled")
                if not bot_task.done():
                    bot_task.cancel()
                    try:
                        await bot_task
                    except asyncio.CancelledError:
                        pass
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                # Keep web server running despite errors
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
                max_retries = 5
                retry_count = 0

                # Добавляем дополнительную задержку для предотвращения конфликтов
                print("⏳ Waiting 10 seconds before starting bot to avoid conflicts...")
                await asyncio.sleep(10)

                while retry_count < max_retries:
                    try:
                        print(f"🤖 Starting bot polling (attempt {retry_count + 1}/{max_retries})...")

                        # Принудительно очищаем все webhook и ждем
                        try:
                            await bot_instance.delete_webhook(drop_pending_updates=True)
                            await asyncio.sleep(8)
                            print("✅ Webhooks cleared")
                        except Exception as webhook_error:
                            print(f"⚠️ Webhook clearing error: {webhook_error}")

                        # Проверяем доступность бота
                        me = await bot_instance.get_me()
                        print(f"✅ Bot connected: @{me.username}")

                        # Дополнительная задержка перед началом polling
                        await asyncio.sleep(3)

                        # Start polling with proper error handling
                        await dp_instance.start_polling(bot_instance, handle_signals=False)
                        break  # Success, exit retry loop

                    except asyncio.CancelledError:
                        print("🛑 Bot polling cancelled")
                        break
                    except Exception as e:
                        retry_count += 1
                        error_msg = str(e).lower()
                        print(f"❌ Bot polling error (attempt {retry_count}): {e}")

                        if "conflict" in error_msg or "terminated by other getupdates" in error_msg:
                            wait_time = 30 + (15 * retry_count)  # Увеличиваем время ожидания
                            print(f"🔄 Bot conflict detected - another instance is running")
                            print(f"💡 Please stop all other bot instances (Railway, other Replit tabs)")
                            print(f"⏳ Waiting {wait_time} seconds before retry...")
                            if retry_count < max_retries:
                                await asyncio.sleep(wait_time)
                            else:
                                print("❌ Max retries reached. Bot conflict persists.")
                                print("🛑 Web app will continue working without bot polling.")
                                break
                        elif retry_count >= max_retries:
                            print(f"❌ Max retries reached. Bot polling failed: {e}")
                            break
                        else:
                            await asyncio.sleep(10)

            # Create bot task but don't wait for it
            bot_task = asyncio.create_task(start_bot_polling())

            # Keep the web server running indefinitely
            print("✅ Replit setup complete - keeping web server alive...")
            try:
                while True:
                    await asyncio.sleep(30)
                    # Check if bot task is still running
                    if bot_task.done():
                        exception = bot_task.exception()
                        if exception:
                            print(f"🔄 Bot task finished with error: {exception}")
                        else:
                            print("✅ Bot task completed")
                        # Don't restart bot task to avoid conflicts
            except asyncio.CancelledError:
                print("🛑 Main loop cancelled")
                if not bot_task.done():
                    bot_task.cancel()
                    try:
                        await bot_task
                    except asyncio.CancelledError:
                        pass
            except Exception as e:
                print(f"❌ Main loop error: {e}")
                # Keep web server running despite errors
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