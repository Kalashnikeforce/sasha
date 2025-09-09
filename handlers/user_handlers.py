from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from config import TIKTOK_LINK, TELEGRAM_LINK, WEB_APP_URL
from database import add_user
import json
from aiogram.filters import Command
from config import CHANNEL_ID

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name, user.last_name)

    # Check if it's a deep link for tournament registration
    args = message.text.split()[1:] if len(message.text.split()) > 1 else []

    if args and args[0].startswith('tournament_'):
        tournament_id = args[0].replace('tournament_', '')

        # Create special keyboard for tournament registration
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎮 Зарегистрироваться в турнире",
                web_app=WebAppInfo(url=f"{WEB_APP_URL}?tournament_id={tournament_id}")
            )],
            [InlineKeyboardButton(text="📱 TikTok", url=TIKTOK_LINK)],
            [InlineKeyboardButton(text="💬 Канал", url=TELEGRAM_LINK)]
        ])

        await message.answer(
            f"🎯 <b>Добро пожаловать в PUBG Bot!</b>\n\n"
            f"Вы перешли для регистрации в турнире.\n"
            f"Нажмите кнопку ниже, чтобы зарегистрироваться!\n\n"
            f"🎮 Участвуйте в турнирах\n"
            f"🎁 Выигрывайте призы\n"
            f"🏆 Становитесь чемпионами!",
            reply_markup=keyboard,
            parse_mode='HTML'
        )
    else:
        # Regular start message
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🎮 Открыть приложение",
                web_app=WebAppInfo(url=WEB_APP_URL)
            )],
            [InlineKeyboardButton(text="📱 TikTok", url=TIKTOK_LINK)],
            [InlineKeyboardButton(text="💬 Канал", url=TELEGRAM_LINK)]
        ])

        await message.answer(
            f"🎯 <b>Добро пожаловать в PUBG Bot!</b>\n\n"
            f"Здесь вы можете:\n"
            f"🎮 Участвовать в турнирах\n"
            f"🎁 Участвовать в розыгрышах\n"
            f"🏆 Выигрывать крутые призы!\n\n"
            f"Нажмите кнопку ниже, чтобы начать:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer(
        "🆘 <b>Помощь</b>\n\n"
        "🎮 <b>Основные функции:</b>\n"
        "• Участие в турнирах PUBG\n"
        "• Участие в розыгрышах призов\n"
        "• Просмотр результатов\n\n"
        "📱 <b>Как пользоваться:</b>\n"
        "1. Нажмите «Открыть приложение»\n"
        "2. Выберите турнир или розыгрыш\n"
        "3. Заполните форму регистрации\n"
        "4. Ждите результатов!\n\n"
        "🏆 Удачи в соревнованиях!",
        parse_mode='HTML'
    )