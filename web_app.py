from aiohttp import web, ClientSession
import json
import aiosqlite
import os
import asyncio
from config import DATABASE_PATH, BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, WEB_APP_URL
import random
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def index_handler(request):
    """Serve the main index.html file"""
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return web.Response(text=content, content_type='text/html')
    except FileNotFoundError:
        return web.json_response({
            "message": "PUBG Bot Web App",
            "status": "running",
            "endpoints": ["/health", "/api/giveaways", "/api/tournaments"]
        })

async def favicon_handler(request):
    """Serve favicon.ico"""
    try:
        favicon_path = 'static/favicon.ico'
        if not os.path.exists(favicon_path):
            return web.Response(status=204)

        with open(favicon_path, 'rb') as f:
            content = f.read()

        return web.Response(body=content, content_type='image/x-icon')
    except Exception as e:
        print(f"❌ Error serving favicon: {e}")
        return web.Response(status=204)

async def serve_script_js(request):
    """Serve script.js file"""
    try:
        script_path = 'static/script.js'
        if not os.path.exists(script_path):
            print(f"❌ Script file not found: {script_path}")
            return web.Response(
                text="console.error('Script file not found');",
                content_type='application/javascript',
                status=404
            )

        print(f"✅ Serving script.js from: {script_path}")

        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return web.Response(
            text=content,
            content_type='application/javascript',
            headers={'Cache-Control': 'no-cache'}
        )
    except Exception as e:
        print(f"❌ Error serving script.js: {e}")
        return web.Response(
            text=f"console.error('Script error: {str(e)}');",
            content_type='application/javascript',
            status=500
        )

async def serve_style_css(request):
    """Serve style.css file"""
    try:
        css_path = 'static/style.css'
        if not os.path.exists(css_path):
            return web.Response(text="/* Styles not found */", content_type='text/css')

        with open(css_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return web.Response(
            text=content,
            content_type='text/css',
            headers={'Cache-Control': 'no-cache'}
        )
    except Exception as e:
        print(f"❌ Error serving style.css: {e}")
        return web.Response(text="/* CSS error */", content_type='text/css')

async def health_check(request):
    """Railway production health check"""
    # Максимально быстрый ответ для Railway production
    return web.json_response({
        "status": "healthy",
        "environment": "production",
        "service": "PUBG Web App",
        "timestamp": datetime.now().isoformat(),
        "ready": True
    }, status=200)

async def create_app(bot):
    app = web.Application()
    app['bot'] = bot

    @web.middleware
    async def cors_middleware(request, handler):
        try:
            if request.method == 'OPTIONS':
                response = web.Response()
            else:
                response = await handler(request)

            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        except Exception as e:
            print(f"❌ CORS middleware error: {e}")
            return web.json_response({'error': 'Server error'}, status=500)

    app.middlewares.append(cors_middleware)

    # Health check for Railway - FIRST priority
    app.router.add_get('/health', health_check)
    app.router.add_get('/favicon.ico', favicon_handler)

    # API routes
    app.router.add_get('/api/giveaways', get_giveaways)
    app.router.add_get('/api/giveaways/{giveaway_id}', get_single_giveaway)
    app.router.add_post('/api/giveaways', create_giveaway)
    app.router.add_put('/api/giveaways/{giveaway_id}', update_giveaway)
    app.router.add_delete('/api/giveaways/{giveaway_id}', delete_giveaway)
    app.router.add_post('/api/giveaways/{giveaway_id}/participate', participate_giveaway)
    app.router.add_post('/api/giveaways/{giveaway_id}/draw', draw_winner)
    app.router.add_post('/api/giveaways/{giveaway_id}/finish', finish_giveaway)
    app.router.add_get('/api/tournaments', get_tournaments)
    app.router.add_post('/api/tournaments', create_tournament)
    app.router.add_delete('/api/tournaments/{tournament_id}', delete_tournament)
    app.router.add_post('/api/tournaments/{tournament_id}/register', register_tournament)
    app.router.add_get('/api/tournaments/{tournament_id}/participants', get_tournament_participants)
    app.router.add_get('/api/stats', get_stats)
    app.router.add_post('/api/check-admin', check_admin)
    app.router.add_post('/api/check-subscription', check_subscription)
    app.router.add_post('/api/tournaments/{tournament_id}/toggle-registration', toggle_tournament_registration)
    app.router.add_post('/api/tournaments/{tournament_id}/announce-winners', announce_tournament_winners)

    # Static file routes
    app.router.add_get('/script.js', serve_script_js)
    app.router.add_get('/style.css', serve_style_css)
    app.router.add_get('/static/script.js', serve_script_js)
    app.router.add_get('/static/style.css', serve_style_css)

    # Serve static files directory
    app.router.add_static('/static', 'static/', name='static')

    # Root route to serve index.html - LAST
    app.router.add_get('/', index_handler)

    return app

async def get_giveaways(request):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       COALESCE(g.winners_count, 1) as winners_count, COUNT(gp.user_id) as participants
                FROM giveaways g
                LEFT JOIN giveaway_participants gp ON g.id = gp.giveaway_id
                WHERE g.is_active = TRUE
                GROUP BY g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, g.winners_count
                ORDER BY g.created_date DESC
            ''')
        except Exception as e:
            print(f"Database error, trying fallback query: {e}")
            # Fallback query without winners_count
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       1 as winners_count, COUNT(gp.user_id) as participants
                FROM giveaways g
                LEFT JOIN giveaway_participants gp ON g.id = gp.giveaway_id
                WHERE g.is_active = TRUE
                GROUP BY g.id, g.title, g.description, g.end_date, g.is_active, g.created_date
                ORDER BY g.created_date DESC
            ''')
        
        giveaways = await cursor.fetchall()

        result = []
        for row in giveaways:
            result.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'end_date': row[3],
                'is_active': row[4],
                'created_date': row[5],
                'winners_count': row[6] if len(row) > 6 else 1,
                'participants': row[7] if len(row) > 7 else row[6]
            })

        return web.json_response(result)

async def get_single_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       COALESCE(g.winners_count, 1) as winners_count, COUNT(gp.user_id) as participants
                FROM giveaways g
                LEFT JOIN giveaway_participants gp ON g.id = gp.giveaway_id
                WHERE g.id = ?
                GROUP BY g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, g.winners_count
            ''', (giveaway_id,))
        except Exception as e:
            print(f"Database error, trying fallback query: {e}")
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       1 as winners_count, COUNT(gp.user_id) as participants
                FROM giveaways g
                LEFT JOIN giveaway_participants gp ON g.id = gp.giveaway_id
                WHERE g.id = ?
                GROUP BY g.id, g.title, g.description, g.end_date, g.is_active, g.created_date
            ''', (giveaway_id,))
        
        giveaway = await cursor.fetchone()
        
        if not giveaway:
            return web.json_response({'error': 'Giveaway not found'}, status=404)

        # Get prizes
        cursor = await db.execute('''
            SELECT place, prize FROM giveaway_prizes 
            WHERE giveaway_id = ? ORDER BY place
        ''', (giveaway_id,))
        prizes = await cursor.fetchall()

        result = {
            'id': giveaway[0],
            'title': giveaway[1],
            'description': giveaway[2],
            'end_date': giveaway[3],
            'is_active': giveaway[4],
            'created_date': giveaway[5],
            'winners_count': giveaway[6] if len(giveaway) > 6 else 1,
            'participants': giveaway[7] if len(giveaway) > 7 else giveaway[6],
            'prizes': [prize[1] for prize in prizes]
        }

        return web.json_response(result)

async def create_giveaway(request):
    data = await request.json()
    bot = request.app['bot']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO giveaways (title, description, end_date, winners_count)
            VALUES (?, ?, ?, ?)
        ''', (data['title'], data['description'], data['end_date'], data.get('winners_count', 1)))
        await db.commit()
        giveaway_id = cursor.lastrowid

        # Save prizes if provided
        if 'prizes' in data and data['prizes']:
            for i, prize in enumerate(data['prizes'], 1):
                if prize.strip():
                    await db.execute('''
                        INSERT INTO giveaway_prizes (giveaway_id, place, prize)
                        VALUES (?, ?, ?)
                    ''', (giveaway_id, i, prize.strip()))
            await db.commit()

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Участвовать", callback_data=f"giveaway_participate_{giveaway_id}")]
    ])

    # Формируем текст с призами
    prizes_text = ""
    if 'prizes' in data and data['prizes']:
        prizes_text = "\n🎁 <b>ПРИЗЫ:</b>\n"
        for i, prize in enumerate(data['prizes'], 1):
            if prize.strip():  # Проверяем что приз не пустой
                if i == 1:
                    prizes_text += f"🥇 {prize}\n"
                elif i == 2:
                    prizes_text += f"🥈 {prize}\n"
                elif i == 3:
                    prizes_text += f"🥉 {prize}\n"
                else:
                    prizes_text += f"🏅 {i} место: {prize}\n"

    post_text = f"""
🎁 <b>НОВЫЙ РОЗЫГРЫШ!</b>

🏆 <b>{data['title']}</b>

📝 {data['description']}
{prizes_text}
📅 Окончание: {data['end_date']}

👥 Участников: 0

Нажми кнопку ниже для участия! 👇
    """

    try:
        # Проверяем доступность канала и права бота
        try:
            chat_info = await bot.get_chat(CHANNEL_ID)
            print(f"✅ Channel found: {chat_info.title}")
            
            bot_member = await bot.get_chat_member(CHANNEL_ID, bot.id)
            print(f"🤖 Bot status in channel: {bot_member.status}")
            
            if bot_member.status not in ['administrator', 'creator']:
                print(f"⚠️ Bot is not admin. Status: {bot_member.status}")
                print(f"💡 Please make @{(await bot.get_me()).username} an administrator in {CHANNEL_ID}")
                return web.json_response({'success': False, 'error': 'Bot is not administrator in channel'})
                
        except Exception as check_error:
            print(f"❌ Channel check failed: {check_error}")
            return web.json_response({'success': False, 'error': f'Cannot access channel: {check_error}'})
        
        # Отправляем сообщение
        message = await bot.send_message(CHANNEL_ID, post_text, reply_markup=keyboard, parse_mode='HTML')
        print(f"✅ Message posted to channel successfully")
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('UPDATE giveaways SET message_id = ? WHERE id = ?', (message.message_id, giveaway_id))
            await db.commit()
            
    except Exception as e:
        print(f"❌ Error posting to channel: {e}")
        return web.json_response({'success': False, 'error': f'Failed to post to channel: {e}'})

    return web.json_response({'success': True, 'id': giveaway_id})

async def update_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']
    data = await request.json()

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE giveaways 
            SET title = ?, description = ?, end_date = ?, winners_count = ?
            WHERE id = ?
        ''', (data['title'], data['description'], data['end_date'], data.get('winners_count', 1), giveaway_id))
        await db.commit()

    return web.json_response({'success': True})

async def delete_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Delete participants first
        await db.execute('DELETE FROM giveaway_participants WHERE giveaway_id = ?', (giveaway_id,))
        # Delete giveaway
        await db.execute('DELETE FROM giveaways WHERE id = ?', (giveaway_id,))
        await db.commit()

    return web.json_response({'success': True})

async def finish_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE giveaways SET is_active = FALSE, status = 'finished' WHERE id = ?
        ''', (giveaway_id,))
        await db.commit()

    return web.json_response({'success': True})

async def participate_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']
    data = await request.json()
    user_id = data['user_id']

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO giveaway_participants (giveaway_id, user_id)
                VALUES (?, ?)
            ''', (giveaway_id, user_id))
            await db.commit()

            cursor = await db.execute('''
                SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id = ?
            ''', (giveaway_id,))
            count = await cursor.fetchone()
            participant_count = count[0] if count else 0

        return web.json_response({'success': True, 'participants': participant_count})
    except:
        return web.json_response({'success': False, 'error': 'Already participated'})

async def get_stats(request):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM users')
        total_users = (await cursor.fetchone())[0]

        cursor = await db.execute('SELECT COUNT(*) FROM users WHERE is_subscribed = TRUE')
        active_users = (await cursor.fetchone())[0]

        cursor = await db.execute('SELECT COUNT(*) FROM giveaways')
        total_giveaways = (await cursor.fetchone())[0]

        cursor = await db.execute('SELECT COUNT(*) FROM tournaments')
        total_tournaments = (await cursor.fetchone())[0]

    return web.json_response({
        'total_users': total_users,
        'active_users': active_users,
        'total_giveaways': total_giveaways,
        'total_tournaments': total_tournaments
    })

async def draw_winner(request):
    giveaway_id = request.match_info['giveaway_id']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Получаем информацию о розыгрыше
        cursor = await db.execute('''
            SELECT winners_count, title FROM giveaways WHERE id = ?
        ''', (giveaway_id,))
        giveaway_info = await cursor.fetchone()
        
        if not giveaway_info:
            return web.json_response({'success': False, 'error': 'Giveaway not found'})
        
        winners_count = giveaway_info[0] or 1
        giveaway_title = giveaway_info[1]

        # Получаем всех участников
        cursor = await db.execute('''
            SELECT gp.user_id, u.first_name, u.username 
            FROM giveaway_participants gp
            JOIN users u ON gp.user_id = u.user_id
            WHERE gp.giveaway_id = ?
        ''', (giveaway_id,))
        participants = await cursor.fetchall()

    if not participants:
        return web.json_response({'success': False, 'error': 'Нет участников для розыгрыша'})

    if len(participants) < winners_count:
        return web.json_response({'success': False, 'error': f'Недостаточно участников. Нужно минимум {winners_count}, а участвует {len(participants)}'})

    # Честный случайный выбор победителей
    import secrets  # Используем криптографически стойкий генератор
    
    # Перемешиваем список участников для максимальной случайности
    participants_list = list(participants)
    for i in range(len(participants_list)):
        j = secrets.randbelow(len(participants_list))
        participants_list[i], participants_list[j] = participants_list[j], participants_list[i]
    
    # Выбираем победителей
    winners = participants_list[:winners_count]

    # Формируем результат
    winners_info = []
    for winner in winners:
        winners_info.append({
            'id': winner[0],
            'name': winner[1] or "Unknown",
            'username': winner[2]
        })

    # Помечаем розыгрыш как завершенный после разыгрывания
    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE giveaways SET is_active = FALSE, status = 'completed' WHERE id = ?
        ''', (giveaway_id,))
        await db.commit()

    # Отправляем уведомления всем участникам
    bot = request.app['bot']
    try:
        # Формируем сообщение для участников
        if len(winners_info) == 1:
            winner_text = f"🏆 Победитель: {winners_info[0]['name']}"
            if winners_info[0]['username']:
                winner_text += f" (@{winners_info[0]['username']})"
        else:
            winner_text = "🏆 Победители:\n"
            for i, winner in enumerate(winners_info, 1):
                winner_text += f"{i}. {winner['name']}"
                if winner['username']:
                    winner_text += f" (@{winner['username']})"
                winner_text += "\n"

        notification_message = f"""
🎉 <b>Розыгрыш завершен!</b>

🎁 <b>{giveaway_title}</b>

{winner_text}

Спасибо всем за участие! 
Следите за новыми розыгрышами! 🚀
        """

        # Отправляем уведомления всем участникам
        for participant in participants:
            try:
                await bot.send_message(
                    participant[0],  # user_id
                    notification_message,
                    parse_mode='HTML'
                )
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
            except Exception as e:
                print(f"Failed to send notification to user {participant[0]}: {e}")
                continue

        print(f"✅ Sent notifications to {len(participants)} participants")

        # Отправляем уведомление в канал о завершении розыгрыша
        try:
            # Проверяем права бота в канале
            try:
                bot_member = await bot.get_chat_member(CHANNEL_ID, bot.id)
                print(f"🤖 Bot status in channel: {bot_member.status}")
                
                if bot_member.status not in ['administrator', 'creator']:
                    print(f"⚠️ Bot is not admin in channel. Status: {bot_member.status}")
                    print(f"💡 Please add @{(await bot.get_me()).username} as administrator to {CHANNEL_ID}")
                    
            except Exception as check_error:
                print(f"❌ Cannot check bot permissions: {check_error}")
            
            channel_message = f"""
🎉 <b>РОЗЫГРЫШ ЗАВЕРШЕН!</b>

🎁 <b>{giveaway_title}</b>

{winner_text}

👥 Всего участников: {len(participants)}

Спасибо всем за участие! 
Следите за новыми розыгрышами! 🚀
            """
            
            await bot.send_message(CHANNEL_ID, channel_message, parse_mode='HTML')
            print("✅ Channel notification sent successfully")
            
        except Exception as channel_error:
            print(f"❌ Error sending channel notification: {channel_error}")
            print(f"💡 Make sure bot @{(await bot.get_me()).username} is added as administrator to {CHANNEL_ID}")

    except Exception as e:
        print(f"❌ Error sending notifications: {e}")

    if len(winners_info) == 1:
        return web.json_response({
            'success': True,
            'winner': winners_info[0],
            'message': f'🎉 Победитель розыгрыша "{giveaway_title}"'
        })
    else:
        return web.json_response({
            'success': True,
            'winners': winners_info,
            'message': f'🎉 Победители розыгрыша "{giveaway_title}" ({len(winners_info)} чел.)'
        })

async def create_tournament(request):
    data = await request.json()
    bot = request.app['bot']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO tournaments (title, description, start_date, winners_count)
            VALUES (?, ?, ?, ?)
        ''', (data['title'], data['description'], data['start_date'], data.get('winners_count', 1)))
        await db.commit()
        tournament_id = cursor.lastrowid

    # Получаем имя бота для создания правильной ссылки
    try:
        bot_info = await bot.get_me()
        bot_username = bot_info.username
    except Exception as e:
        print(f"Error getting bot info: {e}")
        bot_username = "NEIZVESTNY1_BOT"  # fallback

    # Создаем обычную кнопку для регистрации на турнир
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Участвовать в турнире", callback_data=f"tournament_participate_{tournament_id}")]
    ])

    # Формируем текст с призами если они есть
    prizes_text = ""
    if 'prizes' in data and data['prizes']:
        prizes_text = "\n🏅 <b>ПРИЗЫ:</b>\n"
        for i, prize in enumerate(data['prizes'], 1):
            if prize.strip():  # Проверяем что приз не пустой
                if i == 1:
                    prizes_text += f"🥇 {prize}\n"
                elif i == 2:
                    prizes_text += f"🥈 {prize}\n"
                elif i == 3:
                    prizes_text += f"🥉 {prize}\n"
                else:
                    prizes_text += f"🏅 {i} место: {prize}\n"

    post_text = f"""
🏆 <b>НОВЫЙ ТУРНИР PUBG MOBILE!</b>

🎯 <b>{data['title']}</b>

📝 {data['description']}
{prizes_text}
📅 Начало: {data['start_date']}

👥 Участников: 0

Нажми кнопку для участия! 👇
    """

    try:
        # Проверяем доступность канала и права бота
        try:
            chat_info = await bot.get_chat(CHANNEL_ID)
            print(f"✅ Channel found: {chat_info.title}")
            
            bot_member = await bot.get_chat_member(CHANNEL_ID, bot.id)
            print(f"🤖 Bot status in channel: {bot_member.status}")
            
            if bot_member.status not in ['administrator', 'creator']:
                print(f"⚠️ Bot is not admin. Status: {bot_member.status}")
                print(f"💡 Please make @{bot_username} an administrator in {CHANNEL_ID}")
                return web.json_response({'success': False, 'error': 'Bot is not administrator in channel'})
                
        except Exception as check_error:
            print(f"❌ Channel check failed: {check_error}")
            return web.json_response({'success': False, 'error': f'Cannot access channel: {check_error}'})
        
        # Отправляем сообщение
        message = await bot.send_message(CHANNEL_ID, post_text, reply_markup=keyboard, parse_mode='HTML')
        print(f"✅ Tournament posted to channel successfully")
        
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('UPDATE tournaments SET message_id = ? WHERE id = ?', (message.message_id, tournament_id))
            await db.commit()
            
    except Exception as e:
        print(f"❌ Error posting tournament to channel: {e}")
        return web.json_response({'success': False, 'error': f'Failed to post to channel: {e}'})

    return web.json_response({'success': True, 'id': tournament_id})

async def register_tournament(request):
    tournament_id = request.match_info['tournament_id']
    data = await request.json()

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT INTO tournament_participants (tournament_id, user_id, age, phone_brand, nickname, game_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (tournament_id, data['user_id'], data['age'], data['phone_brand'], data['nickname'], data['game_id']))
            await db.commit()

        return web.json_response({'success': True})
    except:
        return web.json_response({'success': False, 'error': 'Already registered'})

async def check_admin(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        is_admin = user_id in ADMIN_IDS if user_id else False
        return web.json_response({'is_admin': is_admin})
    except Exception as e:
        print(f"Error in check_admin: {e}")
        return web.json_response({'is_admin': False})

async def check_subscription(request):
    data = await request.json()
    user_id = data.get('user_id')
    bot = request.app['bot']

    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        is_subscribed = member.status in ['member', 'administrator', 'creator']

        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                INSERT OR IGNORE INTO users (user_id, is_subscribed) VALUES (?, ?)
            ''', (user_id, is_subscribed))
            await db.execute('''
                UPDATE users SET is_subscribed = ? WHERE user_id = ?
            ''', (is_subscribed, user_id))
            await db.commit()

        return web.json_response({'is_subscribed': is_subscribed})
    except Exception as e:
        error_message = str(e).lower()

        # Для публичных каналов или ошибок доступа - считаем подписанным если пользователь есть в базе
        if any(keyword in error_message for keyword in ["member list is inaccessible", "bad request", "forbidden"]):
            try:
                async with aiosqlite.connect(DATABASE_PATH) as db:
                    # Добавляем пользователя если его нет
                    await db.execute('''
                        INSERT OR IGNORE INTO users (user_id, is_subscribed) VALUES (?, ?)
                    ''', (user_id, True))
                    await db.commit()

                    return web.json_response({'is_subscribed': True})
            except Exception as db_error:
                print(f"Database error in subscription check: {db_error}")
                return web.json_response({'is_subscribed': True})

        print(f"Subscription check failed for user {user_id}: {e}")
        return web.json_response({'is_subscribed': False})

async def get_tournaments(request):
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT t.*, COUNT(tp.user_id) as participants
            FROM tournaments t
            LEFT JOIN tournament_participants tp ON t.id = tp.tournament_id
            GROUP BY t.id
            ORDER BY t.created_date DESC
        ''')
        tournaments = await cursor.fetchall()

        result = []
        for row in tournaments:
            result.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'start_date': row[3],
                'created_date': row[4],
                'winners_count': row[5] or 1,
                'registration_status': row[6] or 'open',
                'participants': row[7] or 0
            })

        return web.json_response(result)

async def get_tournament_participants(request):
    tournament_id = request.match_info['tournament_id']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT tp.*, u.first_name, u.username
            FROM tournament_participants tp
            JOIN users u ON tp.user_id = u.user_id
            WHERE tp.tournament_id = ?
            ORDER BY tp.registration_date DESC
        ''', (tournament_id,))
        participants = await cursor.fetchall()

        result = []
        for row in participants:
            result.append({
                'id': row[0],
                'tournament_id': row[1],
                'user_id': row[2],
                'age': row[3],
                'phone_brand': row[4],
                'nickname': row[5],
                'game_id': row[6],
                'registration_date': row[7],
                'first_name': row[8],
                'username': row[9]
            })

        return web.json_response(result)

async def toggle_tournament_registration(request):
    try:
        tournament_id = request.match_info['tournament_id']
        data = await request.json()
        new_status = data.get('status', 'open')

        print(f"🔄 Toggling tournament {tournament_id} registration to: {new_status}")

        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check if tournament exists and get current status
            cursor = await db.execute('SELECT id, registration_status FROM tournaments WHERE id = ?', (tournament_id,))
            tournament = await cursor.fetchone()
            
            if not tournament:
                print(f"❌ Tournament {tournament_id} not found")
                return web.json_response({'success': False, 'error': 'Tournament not found'}, status=404)
            
            old_status = tournament[1] if tournament[1] else 'open'
            print(f"📊 Current status: {old_status}, New status: {new_status}")
            
            # Update registration status
            await db.execute('''
                UPDATE tournaments SET registration_status = ? WHERE id = ?
            ''', (new_status, tournament_id))
            await db.commit()
            
            # Verify update
            cursor = await db.execute('SELECT registration_status FROM tournaments WHERE id = ?', (tournament_id,))
            updated_tournament = await cursor.fetchone()
            updated_status = updated_tournament[0] if updated_tournament else 'open'
            
            print(f"✅ Tournament {tournament_id} registration updated from {old_status} to {updated_status}")

        return web.json_response({'success': True, 'status': new_status, 'updated_status': updated_status})
    except Exception as e:
        print(f"❌ Error toggling tournament registration: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def delete_tournament(request):
    tournament_id = request.match_info['tournament_id']

    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Check if tournament exists
            cursor = await db.execute('SELECT id FROM tournaments WHERE id = ?', (tournament_id,))
            tournament = await cursor.fetchone()
            
            if not tournament:
                return web.json_response({'success': False, 'error': 'Tournament not found'}, status=404)
            
            # Delete participants first
            await db.execute('DELETE FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
            # Delete tournament
            await db.execute('DELETE FROM tournaments WHERE id = ?', (tournament_id,))
            await db.commit()
            
            print(f"✅ Tournament {tournament_id} deleted successfully")

        return web.json_response({'success': True})
    except Exception as e:
        print(f"❌ Error deleting tournament: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)

async def announce_tournament_winners(request):
    tournament_id = request.match_info['tournament_id']
    data = await request.json()
    winners_text = data.get('winners', '')
    
    bot = request.app['bot']
    
    try:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            # Получаем информацию о турнире
            cursor = await db.execute('SELECT title FROM tournaments WHERE id = ?', (tournament_id,))
            tournament = await cursor.fetchone()
            
            if not tournament:
                return web.json_response({'success': False, 'error': 'Tournament not found'})
            
            tournament_title = tournament[0]
            
            # Получаем количество участников
            cursor = await db.execute('SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
            participants_count = (await cursor.fetchone())[0]

        # Отправляем объявление о победителях в канал
        announcement = f"""
🏆 <b>ТУРНИР ЗАВЕРШЕН!</b>

🎯 <b>{tournament_title}</b>

🏅 <b>ПОБЕДИТЕЛИ:</b>
{winners_text}

👥 Всего участников: {participants_count}

Поздравляем победителей! 🎉
Следите за новыми турнирами! 🚀
        """
        
        await bot.send_message(CHANNEL_ID, announcement, parse_mode='HTML')
        
        return web.json_response({'success': True})
        
    except Exception as e:
        print(f"Error announcing tournament winners: {e}")
        return web.json_response({'success': False, 'error': str(e)})