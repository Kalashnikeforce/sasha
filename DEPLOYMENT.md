
# 🚀 Deployment Workflow

## Архитектура проекта

### Railway (Продакшн) 🌐
- **Назначение**: Публичное приложение для пользователей
- **URL**: https://sasha-production.up.railway.app
- **Функции**: Полный функционал (веб + бот)
- **Режим**: PRODUCTION

### Replit (Разработка) 🔧
- **Назначение**: Среда разработки и тестирования
- **Функции**: Полный функционал (веб + бот)
- **Режим**: DEVELOPMENT

## Рабочий процесс

### 1. Разработка на Replit
```bash
# Запустить полную версию с ботом
python main.py
```

### 2. Тестирование на Replit
- Тестируйте все изменения локально
- Проверяйте работу бота и веб-интерфейса

### 3. Деплой на Railway
1. Остановите бота на Replit (чтобы избежать конфликтов)
2. Загрузите изменения в Git
3. Railway автоматически задеплоит обновления
4. Проверьте работу веб-интерфейса в продакшне

## Переменные окружения

### Railway Production
```
BOT_TOKEN=your_bot_token
ADMIN_IDS=7131412293
RAILWAY_ENVIRONMENT=production
```

### Replit Development
```
BOT_TOKEN=your_bot_token
ADMIN_IDS=7131412293
```

## Команды для разработки

### Запуск на Replit (development)
- Полный функционал: веб + бот
- URL: https://workspace.CryptoGurman.repl.co

### Проверка Railway (production)
- Полный функционал: веб + бот
- URL: https://sasha-production.up.railway.app
- Health check: /health

## Рекомендации

1. **Всегда разрабатывайте на Replit**
2. **Railway используйте только как production**
3. **Не запускайте бота одновременно в двух местах**
4. **Тестируйте изменения перед деплоем на Railway**
