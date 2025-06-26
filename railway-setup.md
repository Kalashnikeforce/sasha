
# Railway Deployment Setup

## Environment Variables для Railway:

```
BOT_TOKEN=your_bot_token_from_botfather
ADMIN_IDS=123456789,987654321
RAILWAY_ENVIRONMENT=production
```

## Настройка:

1. Подключите GitHub репозиторий к Railway
2. Добавьте переменные окружения в Railway Dashboard
3. Railway автоматически назначит домен
4. Обновите URL веб-приложения в BotFather

## После деплоя:

1. Скопируйте назначенный Railway домен
2. Перейдите к @BotFather
3. Выберите ваш бот → Bot Settings → Menu Button
4. Укажите URL: https://your-railway-domain.railway.app

Ваш бот будет работать 24/7 на Railway!
