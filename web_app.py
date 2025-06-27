from aiohttp import web, ClientSession
import json
import aiosqlite
import os
from config import DATABASE_PATH, BOT_TOKEN, CHANNEL_ID, ADMIN_IDS
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
    """Ultra-fast health check for Railway"""
    try:
        # Быстрый ответ без дополнительных проверок для Railway
        response_data = {
            "status": "healthy",
            "service": "PUBG Bot Web App",
            "timestamp": datetime.now().isoformat(),
            "ready": True
        }
        
        return web.json_response(response_data, status=200)
        
    except Exception as e:
        # Всегда возвращаем 200 для прохождения healthcheck
        return web.json_response({
            "status": "ok", 
            "service": "PUBG Bot Web App",
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
    app.router.add_post('/api/giveaways', create_giveaway)
    app.router.add_put('/api/giveaways/{giveaway_id}', update_giveaway)
    app.router.add_delete('/api/giveaways/{giveaway_id}', delete_giveaway)
    app.router.add_post('/api/giveaways/{giveaway_id}/participate', participate_giveaway)
    app.router.add_post('/api/giveaways/{giveaway_id}/draw', draw_winner)
    app.router.add_post('/api/giveaways/{giveaway_id}/finish', finish_giveaway)
    app.router.add_get('/api/tournaments', get_tournaments)
    app.router.add_post('/api/tournaments', create_tournament)
    app.router.add_post('/api/tournaments/{tournament_id}/register', register_tournament)
    app.router.add_get('/api/tournaments/{tournament_id}/participants', get_tournament_participants)
    app.router.add_get('/api/stats', get_stats)
    app.router.add_post('/api/check-admin', check_admin)
    app.router.add_post('/api/check-subscription', check_subscription)
    app.router.add_post('/api/tournaments/{tournament_id}/toggle-registration', toggle_tournament_registration)

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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Участвовать", callback_data=f"participate_{giveaway_id}")]
    ])

    post_text = f"""
🎁 <b>НОВЫЙ РОЗЫГРЫШ!</b>

🏆 <b>{data['title']}</b>

📝 {data['description']}

📅 Окончание: {data['end_date']}

👥 Участников: 0

Нажми кнопку ниже для участия! 👇
    """

    try:
        message = await bot.send_message(CHANNEL_ID, post_text, reply_markup=keyboard, parse_mode='HTML')
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('UPDATE giveaways SET message_id = ? WHERE id = ?', (message.message_id, giveaway_id))
            await db.commit()
    except Exception as e:
        print(f"Error posting to channel: {e}")

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
        cursor = await db.execute('''
            SELECT user_id FROM giveaway_participants WHERE giveaway_id = ?
        ''', (giveaway_id,))
        participants = await cursor.fetchall()

    if not participants:
        return web.json_response({'success': False, 'error': 'No participants'})

    winner_id = random.choice(participants)[0]

    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('''
            SELECT first_name, username FROM users WHERE user_id = ?
        ''', (winner_id,))
        winner_info = await cursor.fetchone()

    winner_name = winner_info[0] if winner_info else "Unknown"
    winner_username = winner_info[1] if winner_info and winner_info[1] else None

    return web.json_response({
        'success': True,
        'winner': {
            'id': winner_id,
            'name': winner_name,
            'username': winner_username
        }
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏆 Зарегистрироваться", url=f"https://t.me/your_bot_username?start=tournament_{tournament_id}")]
    ])

    post_text = f"""
🏆 <b>НОВЫЙ ТУРНИР PUBG MOBILE!</b>

🎯 <b>{data['title']}</b>

📝 {data['description']}

📅 Начало: {data['start_date']}

Нажми кнопку для регистрации! 👇
    """

    try:
        await bot.send_message(CHANNEL_ID, post_text, reply_markup=keyboard, parse_mode='HTML')
    except Exception as e:
        print(f"Error posting tournament to channel: {e}")

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
    tournament_id = request.match_info['tournament_id']
    data = await request.json()
    new_status = data.get('status', 'open')

    async with aiosqlite.connect(DATABASE_PATH) as db:
        await db.execute('''
            UPDATE tournaments SET registration_status = ? WHERE id = ?
        ''', (new_status, tournament_id))
        await db.commit()

    return web.json_response({'success': True, 'status': new_status})