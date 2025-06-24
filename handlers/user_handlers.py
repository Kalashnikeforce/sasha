
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.filters import CommandStart
from config import TIKTOK_LINK, TELEGRAM_LINK, WEB_APP_URL
from database import add_user
import json

router = Router()

def register_user_handlers(dp, bot):
    dp.include_router(router)

@router.message(CommandStart())
async def start_command(message: Message):
    user = message.from_user
    await add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Create web app button
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
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode='HTML')и на кнопку ниже, чтобы открыть приложение!
    """
    
    await message.answer(welcome_text, reply_markup=keyboard, parse_mode='HTML')
