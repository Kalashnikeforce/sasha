
from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from config import ADMIN_IDS
import json

router = Router()

def register_admin_handlers(dp, bot):
    dp.include_router(router)

def is_admin(user_id):
    return user_id in ADMIN_IDS

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Создать розыгрыш", callback_data="create_giveaway")],
        [InlineKeyboardButton(text="🏆 Создать турнир", callback_data="create_tournament")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="show_stats")],
        [InlineKeyboardButton(text="⚙️ Управление", callback_data="manage")]
    ])
    
    await message.answer("🔧 <b>Админ-панель PUBG Розыгрышей</b>", reply_markup=keyboard, parse_mode='HTML')
