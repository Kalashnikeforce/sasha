from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from config import TIKTOK_LINK, TELEGRAM_LINK, WEB_APP_URL
from database import add_user
import json
import aiosqlite
from aiogram.filters import Command
from config import DATABASE_PATH, CHANNEL_ID

router = Router()

def register_user_handlers(dp, bot):
    dp.include_router(router)

@router.message(CommandStart())
async def start_command(message: Message):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name, user.last_name)

    # Проверяем есть ли параметр для турнира
    command_args = message.text.split()
    if len(command_args) > 1 and command_args[1].startswith('tournament_'):
        try:
            tournament_id = command_args[1].split('_')[1]
        except IndexError:
            await message.answer("Неверный формат ID турнира.")
            return
        try:
            tournament_id = int(tournament_id)
        except ValueError:
            await message.answer("Некорректный ID турнира.")
            return

        try:
            # Get tournament info and check registration status
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute('SELECT title, registration_status FROM tournaments WHERE id = ?', (tournament_id,))
                tournament = await cursor.fetchone()

            if tournament:
                tournament_title = tournament[0]
                registration_status = tournament[1] if len(tournament) > 1 else 'open'

                # Проверяем статус регистрации
                if registration_status == 'closed':
                    await message.answer(
                        f"❌ <b>Регистрация на турнир закрыта!</b>\n\n"
                        f"🏆 Турнир: {tournament_title}\n\n"
                        f"Следите за новыми турнирами в нашем канале!",
                        parse_mode='HTML'
                    )
                    return

                web_app_url = f"{WEB_APP_URL}?tournament={tournament_id}"
                web_app = WebAppInfo(url=web_app_url)
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🏆 Участвовать в турнире", web_app=web_app)],
                    [
                        InlineKeyboardButton(text="📱 TikTok", url=TIKTOK_LINK),
                        InlineKeyboardButton(text="📢 Telegram", url=TELEGRAM_LINK)
                    ]
                ])

                await message.answer(
                    f"🏆 <b>Турнир: {tournament_title}</b>\n\n"
                    f"✅ Регистрация открыта!\n\n"
                    f"Для участия в турнире нажмите кнопку ниже и заполните регистрационную форму!\n\n"
                    f"📝 Потребуется указать:\n"
                    f"• Возраст\n"
                    f"• Модель телефона\n"
                    f"• Игровой никнейм\n"
                    f"• ID в игре",
                    reply_markup=keyboard,
                    parse_mode='HTML'
                )
                return
            else:
                await message.answer("❌ Турнир не найден!")

        except Exception as e:
            print(f"Error processing tournament start: {e}")
            await message.answer("Произошла ошибка при обработке турнира.")
            # Fallback to normal start

    # Обычный старт
    web_app = WebAppInfo(url=WEB_APP_URL)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Открыть PUBG Розыгрыши", web_app=web_app)],
        [
            InlineKeyboardButton(text="📱 TikTok", url=TIKTOK_LINK),
            InlineKeyboardButton(text="📢 Telegram", url=TELEGRAM_LINK)
        ]
    ])

    welcome_text = f"""
🎮 <b>Добро пожаловать в PUBG Mobile Розыгрыши!</b>

Привет, {user.first_name}! 👋

🏆 Участвуй в розыгрышах
🎯 Регистрируйся на турниры
💎 Выигрывай крутые призы

Нажми кнопку ниже, чтобы открыть приложение! 👇
    """

    await message.answer(welcome_text, reply_markup=keyboard, parse_mode='HTML')