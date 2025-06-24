
from .user_handlers import register_user_handlers
from .admin_handlers import register_admin_handlers

def register_handlers(dp, bot):
    register_user_handlers(dp, bot)
    register_admin_handlers(dp, bot)
