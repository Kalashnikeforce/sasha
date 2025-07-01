from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from config import TIKTOK_LINK, TELEGRAM_LINK, WEB_APP_URL
from database import add_user
import json

router = Router()

def register_user_handlers(dp, bot):
    dp.include_router(router)

@router.message(F.text == "/myid")
async def get_my_id(message: Message):
    """Команда для получения своего Telegram ID"""
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    first_name = message.from_user.first_name or "без имени"
    
    await message.answer(
        f"📋 <b>Твоя информация:</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Username:</b> @{username}\n"
        f"📝 <b>Имя:</b> {first_name}\n\n"
        f"💡 Скопируй ID для настройки админки!",
        parse_mode='HTML'
    )

@router.message(CommandStart())
async def start_command(message: Message):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name, user.last_name)

    # Проверяем есть ли параметр для турнира
    command_args = message.text.split()
    if len(command_args) > 1 and command_args[1].startswith('tournament_'):
        try:
            tournament_id = command_args[1].split('_')[1]
            # Создаем веб-приложение с параметром турнира
            web_app_url = f"{WEB_APP_URL}?tournament={tournament_id}"
            web_app = WebAppInfo(url=web_app_url)

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🏆 Зарегистрироваться на турнир", web_app=web_app)],
                [
                    InlineKeyboardButton(text="📱 TikTok", url=TIKTOK_LINK),
                    InlineKeyboardButton(text="📢 Telegram", url=TELEGRAM_LINK)
                ]
            ])

            tournament_text = f"""
🏆 <b>Регистрация на турнир!</b>

Привет, {user.first_name}! 👋

🎯 Ты переходишь к регистрации на турнир
📝 Заполни все необходимые данные
🏅 Участвуй и выигрывай призы!

Нажми кнопку ниже для регистрации! 👇
            """

            await message.answer(tournament_text, reply_markup=keyboard, parse_mode='HTML')
            return

        except Exception as e:
            print(f"Error processing tournament start: {e}")
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