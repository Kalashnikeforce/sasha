from aiohttp import web, ClientSession
import json
import aiosqlite
import os
import asyncio
from config import DATABASE_PATH, BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, WEB_APP_URL
import random
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import USE_REPLIT_DB, replit_db

# Database helper functions
async def db_execute_query(query, params=None):
    """Execute a query and return results"""
    if USE_REPLIT_DB:
        # Handle Replit DB operations
        return await handle_replit_db_query(query, params)
    else:
        # Handle SQLite operations
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(query, params or ())
            return await cursor.fetchall()

async def db_execute_update(query, params=None):
    """Execute an update query"""
    if USE_REPLIT_DB:
        return await handle_replit_db_update(query, params)
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            cursor = await db.execute(query, params or ())
            await db.commit()
            return cursor.lastrowid

async def handle_replit_db_query(query, params):
    """Handle SELECT queries for Replit DB"""
    query_lower = query.lower().strip()

    if 'select count(*) from giveaways' in query_lower:
        keys = await replit_db.list_keys("giveaway_")
        active_count = 0
        for key in keys:
            giveaway = await replit_db.get(key)
            if giveaway and giveaway.get('is_active', True):
                active_count += 1
        return [(active_count,)]

    elif 'select count(*) from tournaments' in query_lower:
        keys = await replit_db.list_keys("tournament_")
        return [(len(keys),)]

    elif 'select count(*) from users' in query_lower:
        keys = await replit_db.list_keys("user_")
        if 'is_subscribed = true' in query_lower:
            subscribed_count = 0
            for key in keys:
                user = await replit_db.get(key)
                if user and user.get('is_subscribed'):
                    subscribed_count += 1
            return [(subscribed_count,)]
        return [(len(keys),)]

    elif 'from giveaways' in query_lower and 'where g.is_active = true' in query_lower:
        keys = await replit_db.list_keys("giveaway_")
        results = []
        for key in keys:
            giveaway = await replit_db.get(key)
            if giveaway and giveaway.get('is_active', True):
                # Get participant count
                participant_keys = await replit_db.list_keys(f"giveaway_participant_{giveaway['id']}_")
                participant_count = len(participant_keys)

                results.append((
                    giveaway['id'],
                    giveaway['title'],
                    giveaway['description'],
                    giveaway['end_date'],
                    giveaway['is_active'],
                    giveaway['created_date'],
                    giveaway.get('winners_count', 1),
                    participant_count
                ))
        return results

    elif 'from tournaments' in query_lower and 'group by t.id' in query_lower:
        keys = await replit_db.list_keys("tournament_")
        results = []
        for key in keys:
            tournament = await replit_db.get(key)
            if tournament:
                # Get participant count
                participant_keys = await replit_db.list_keys(f"tournament_participant_{tournament['id']}_")
                participant_count = len(participant_keys)

                results.append((
                    tournament['id'],
                    tournament['title'],
                    tournament['description'],
                    tournament['start_date'],
                    tournament['created_date'],
                    tournament.get('winners_count', 1),
                    tournament.get('registration_status', 'open'),
                    participant_count
                ))
        return results

    return []

async def handle_replit_db_update(query, params):
    """Handle INSERT/UPDATE/DELETE queries for Replit DB"""
    query_lower = query.lower().strip()

    if query_lower.startswith('insert into giveaways'):
        # Create new giveaway
        giveaway_id = random.randint(1000, 999999)
        giveaway_data = {
            'id': giveaway_id,
            'title': params[0] if params else '',
            'description': params[1] if len(params) > 1 else '',
            'end_date': params[2] if len(params) > 2 else '',
            'winners_count': params[3] if len(params) > 3 else 1,
            'is_active': True,
            'created_date': datetime.now().isoformat(),
            'status': 'active'
        }
        await replit_db.set(f"giveaway_{giveaway_id}", giveaway_data)
        return giveaway_id

    elif query_lower.startswith('insert into tournaments'):
        # Create new tournament
        tournament_id = random.randint(1000, 999999)
        tournament_data = {
            'id': tournament_id,
            'title': params[0] if params else '',
            'description': params[1] if len(params) > 1 else '',
            'start_date': params[2] if len(params) > 2 else '',
            'winners_count': params[3] if len(params) > 3 else 1,
            'created_date': datetime.now().isoformat(),
            'registration_status': 'open'
        }
        await replit_db.set(f"tournament_{tournament_id}", tournament_data)
        return tournament_id

    elif 'delete from giveaways where id' in query_lower:
        giveaway_id = params[0] if params else None
        if giveaway_id:
            await replit_db.delete(f"giveaway_{giveaway_id}")
            # Delete related participants
            participant_keys = await replit_db.list_keys(f"giveaway_participant_{giveaway_id}_")
            for key in participant_keys:
                await replit_db.delete(key)
        return giveaway_id

    elif 'delete from tournaments where id' in query_lower:
        tournament_id = params[0] if params else None
        if tournament_id:
            await replit_db.delete(f"tournament_{tournament_id}")
            # Delete related participants
            participant_keys = await replit_db.list_keys(f"tournament_participant_{tournament_id}_")
            for key in participant_keys:
                await replit_db.delete(key)
        return tournament_id

    return None

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
    app.router.add_get('/api/tournaments/{tournament_id}', get_single_tournament)

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
    try:
        giveaways = await db_execute_query('''
            SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                   COALESCE(g.winners_count, 1) as winners_count, 
                   (SELECT COUNT(*) FROM giveaway_participants gp WHERE gp.giveaway_id = g.id) as participants
            FROM giveaways g
            WHERE g.is_active = TRUE
            ORDER BY g.created_date DESC
        ''')

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
    except Exception as e:
        print(f"Error loading giveaways: {e}")
        return web.json_response([])

async def get_single_tournament(request):
    tournament_id = request.match_info['tournament_id']

    try:
        if USE_REPLIT_DB:
            tournament = await replit_db.get(f"tournament_{tournament_id}")
            if tournament:
                return web.json_response(tournament)
            else:
                return web.json_response({'error': 'Tournament not found'}, status=404)
        else:
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute('''
                    SELECT id, title, description, start_date, created_date, 
                           winners_count, registration_status
                    FROM tournaments WHERE id = ?
                ''', (tournament_id,))
                tournament = await cursor.fetchone()

                if not tournament:
                    return web.json_response({'error': 'Tournament not found'}, status=404)

                return web.json_response({
                    'id': tournament[0],
                    'title': tournament[1],
                    'description': tournament[2],
                    'start_date': tournament[3],
                    'created_date': tournament[4],
                    'winners_count': tournament[5],
                    'registration_status': tournament[6] or 'open'
                })
    except Exception as e:
        print(f"Error getting tournament: {e}")
        return web.json_response({'error': 'Server error'}, status=500)

async def get_single_giveaway(request):
    giveaway_id = request.match_info['giveaway_id']

    async with aiosqlite.connect(DATABASE_PATH) as db:
        try:
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       COALESCE(g.winners_count, 1) as winners_count,
                       (SELECT COUNT(*) FROM giveaway_participants gp WHERE gp.giveaway_id = g.id) as participants
                FROM giveaways g
                WHERE g.id = ?
            ''', (giveaway_id,))
        except Exception as e:
            print(f"Database error, trying fallback query: {e}")
            cursor = await db.execute('''
                SELECT g.id, g.title, g.description, g.end_date, g.is_active, g.created_date, 
                       1 as winners_count,
                       (SELECT COUNT(*) FROM giveaway_participants gp WHERE gp.giveaway_id = g.id) as participants
                FROM giveaways g
                WHERE g.id = ?
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
        [InlineKeyboardButton(text="🎮 Участвовать (0)", callback_data=f"giveaway_participate_{giveaway_id}")]
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
    try:
        giveaway_id = request.match_info['giveaway_id']

        # Валидация giveaway_id
        try:
            giveaway_id = int(giveaway_id)
        except ValueError:
            print(f"❌ Invalid giveaway_id: {giveaway_id}")
            return web.json_response({'success': False, 'error': 'Invalid giveaway ID'}, status=400)

        # Получаем данные
        try:
            data = await request.json()
        except Exception as e:
            print(f"❌ Error parsing JSON: {e}")
            return web.json_response({'success': False, 'error': 'Invalid JSON data'}, status=400)

        user_id = data.get('user_id')
        if not user_id:
            return web.json_response({'success': False, 'error': 'User ID is required'}, status=400)

        print(f"🎮 Processing participation: giveaway_id={giveaway_id}, user_id={user_id}")

        # Проверяем что розыгрыш существует и активен
        if USE_REPLIT_DB:
            giveaway = await replit_db.get(f"giveaway_{giveaway_id}")
            if not giveaway:
                return web.json_response({'success': False, 'error': 'Giveaway not found'}, status=404)
            if not giveaway.get('is_active', True):
                return web.json_response({'success': False, 'error': 'Giveaway is not active'}, status=400)

            # Проверяем участие в Replit DB
            participant_key = f"giveaway_participant_{giveaway_id}_{user_id}"
            existing = await replit_db.get(participant_key)
            if existing:
                return web.json_response({'success': False, 'error': 'Already participated'})

            # Добавляем участника
            await replit_db.set(participant_key, {
                'giveaway_id': giveaway_id,
                'user_id': user_id,
                'timestamp': datetime.now().isoformat()
            })

            # Считаем участников
            keys = await replit_db.list_keys(f"giveaway_participant_{giveaway_id}_")
            participant_count = len(keys)

        else:
            # SQLite версия
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Проверяем что розыгрыш существует и активен
                cursor = await db.execute('''
                    SELECT is_active FROM giveaways WHERE id = ?
                ''', (giveaway_id,))
                giveaway = await cursor.fetchone()

                if not giveaway:
                    return web.json_response({'success': False, 'error': 'Giveaway not found'}, status=404)

                if not giveaway[0]:  # is_active = False
                    return web.json_response({'success': False, 'error': 'Giveaway is not active'}, status=400)

                # Проверяем участие
                cursor = await db.execute('''
                    SELECT id FROM giveaway_participants WHERE giveaway_id = ? AND user_id = ?
                ''', (giveaway_id, user_id))
                existing = await cursor.fetchone()

                if existing:
                    return web.json_response({'success': False, 'error': 'Already participated'})

                # Добавляем участника
                await db.execute('''
                    INSERT INTO giveaway_participants (giveaway_id, user_id)
                    VALUES (?, ?)
                ''', (giveaway_id, user_id))
                await db.commit()

                # Считаем участников
                cursor = await db.execute('''
                    SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id = ?
                ''', (giveaway_id,))
                count = await cursor.fetchone()
                participant_count = count[0] if count else 0

        print(f"✅ User {user_id} successfully participated in giveaway {giveaway_id}. Total participants: {participant_count}")
        return web.json_response({'success': True, 'participants': participant_count})

    except Exception as e:
        print(f"❌ Error in participate_giveaway: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({'success': False, 'error': 'Server error occurred'}, status=500)

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

    if USE_REPLIT_DB:
        # Replit DB version
        giveaway = await replit_db.get(f"giveaway_{giveaway_id}")
        if not giveaway:
            return web.json_response({'success': False, 'error': 'Giveaway not found'})

        winners_count = giveaway.get('winners_count', 1)
        giveaway_title = giveaway.get('title', 'Розыгрыш')

        # Получаем всех участников
        participant_keys = await replit_db.list_keys(f"giveaway_participant_{giveaway_id}_")
        participant_ids = []
        for key in participant_keys:
            participant_data = await replit_db.get(key)
            if participant_data:
                participant_ids.append(participant_data['user_id'])

        total_participants_count = len(participant_ids)

        if total_participants_count < winners_count:
            return web.json_response({
                'success': False, 
                'error': f'Недостаточно участников! Нужно минимум {winners_count}, а участвует {total_participants_count}'
            })

        # Выбираем случайных победителей
        winner_ids = random.sample(participant_ids, winners_count)

        # Получаем информацию о победителях
        winners = []
        for user_id in winner_ids:
            user_data = await replit_db.get(f"user_{user_id}")
            if user_data:
                first_name = user_data.get('first_name', f"User {user_id}")
                username = user_data.get('username')
                winners.append((user_id, first_name, username))
            else:
                winners.append((user_id, f"User {user_id}", None))

    else:
        # SQLite version
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
                SELECT DISTINCT gp.user_id
                FROM giveaway_participants gp
                WHERE gp.giveaway_id = ?
            ''', (giveaway_id,))
            participant_rows = await cursor.fetchall()
            participant_ids = [row[0] for row in participant_rows]

            total_participants_count = len(participant_ids)

            if total_participants_count < winners_count:
                return web.json_response({
                    'success': False, 
                    'error': f'Недостаточно участников! Нужно минимум {winners_count}, а участвует {total_participants_count}'
                })

            # Выбираем случайных победителей
            winner_ids = random.sample(participant_ids, winners_count)

            # Получаем информацию о победителях
            winners = []
            for user_id in winner_ids:
                cursor = await db.execute('''
                    SELECT first_name, username FROM users WHERE user_id = ?
                ''', (user_id,))
                user_info = await cursor.fetchone()

                if user_info:
                    first_name, username = user_info
                    winners.append((user_id, first_name, username))
                else:
                    winners.append((user_id, f"User {user_id}", None))

            # Сохраняем победителей в базу данных
            for i, winner in enumerate(winners):
                user_id, first_name, username = winner
                display_name = first_name or f"User {user_id}"

                await db.execute('''
                    INSERT INTO giveaway_winners (giveaway_id, user_id, place, name, username)
                    VALUES (?, ?, ?, ?, ?)
                ''', (giveaway_id, user_id, i + 1, display_name, username))

            await db.commit()

    # Формируем результат
    winners_info = []
    for winner in winners:
        winners_info.append({
            'id': winner[0],
            'name': winner[1] or "Unknown",
            'username': winner[2]
        })

    # Помечаем розыгрыш как завершенный
    if USE_REPLIT_DB:
        giveaway['is_active'] = False
        giveaway['status'] = 'completed'
        await replit_db.set(f"giveaway_{giveaway_id}", giveaway)
    else:
        async with aiosqlite.connect(DATABASE_PATH) as db:
            await db.execute('''
                UPDATE giveaways SET is_active = FALSE, status = 'completed' WHERE id = ?
            ''', (giveaway_id,))
            await db.commit()

    # Отправляем уведомления
    bot = request.app['bot']
    try:
        # Формируем сообщение для участников
        if len(winners_info) == 1:
            winner = winners_info[0]
            if winner['username']:
                winner_text = f"🏆 Победитель: @{winner['username']}"
            else:
                winner_text = f"🏆 Победитель: {winner['name']}"
        else:
            winner_text = "🏆 Победители:\n"
            for i, winner in enumerate(winners_info, 1):
                if winner['username']:
                    winner_text += f"{i}. @{winner['username']}\n"
                else:
                    winner_text += f"{i}. {winner['name']}\n"

        notification_message = f"""
🎉 <b>Розыгрыш завершен!</b>

🎁 <b>{giveaway_title}</b>

{winner_text}

Спасибо всем за участие! 
Следите за новыми розыгрышами! 🚀
        """

        # Отправляем уведомления всем участникам
        notifications_sent = 0
        for user_id in participant_ids:
            try:
                await bot.send_message(
                    user_id,
                    notification_message,
                    parse_mode='HTML'
                )
                notifications_sent += 1
                await asyncio.sleep(0.1)  # Небольшая задержка между отправками
            except Exception as e:
                print(f"Failed to send notification to user {user_id}: {e}")
                continue

        print(f"✅ Sent notifications to {notifications_sent}/{total_participants_count} participants")

        # Отправляем уведомление в канал о завершении розыгрыша
        try:
            # Проверяем права бота в канале
            try:
                bot_member = await bot.get_chat_member(CHANNEL_ID, bot.id)
                print(f"🤖 Bot status in channel: {bot_member.status}")

                if bot_member.status not in ['administrator', 'creator']:
                    print(f"⚠️ Bot is not admin in channel. Status: {bot_member.status}")
                    bot_me = await bot.get_me()
                    print(f"💡 Please add @{bot_me.username} as administrator to {CHANNEL_ID}")

            except Exception as check_error:
                print(f"❌ Cannot check bot permissions: {check_error}")

            channel_message = f"""
🎉 <b>РОЗЫГРЫШ ЗАВЕРШЕН!</b>

🎁 <b>{giveaway_title}</b>

{winner_text}

👥 Всего участников: {total_participants_count}

Спасибо всем за участие! 
Следите за новыми розыгрышами! 🚀
            """

            await bot.send_message(CHANNEL_ID, channel_message, parse_mode='HTML')
            print("✅ Channel notification sent successfully")

        except Exception as channel_error:
            print(f"❌ Error sending channel notification: {channel_error}")
            bot_me = await bot.get_me()
            print(f"💡 Make sure bot @{bot_me.username} is added as administrator to {CHANNEL_ID}")

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

    # Get participant count for the button
    async with aiosqlite.connect(DATABASE_PATH) as db:
        cursor = await db.execute('SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ?', (tournament_id,))
        participants_count = (await cursor.fetchone())[0]

    # Создаем кнопку для регистрации на турнир через бота
    # Используем deep link для открытия диалога с ботом
    bot_link = f"https://t.me/{bot_username}?start=tournament_{tournament_id}"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🏆 Участвовать ({participants_count})", url=bot_link)]
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
        if USE_REPLIT_DB:
            # Check tournament status in Replit DB
            tournament = await replit_db.get(f"tournament_{tournament_id}")
            if not tournament:
                return web.json_response({'success': False, 'error': 'Tournament not found'})

            if tournament.get('registration_status') == 'closed':
                return web.json_response({'success': False, 'error': 'Registration is closed'})

            # Check if already registered
            participant_key = f"tournament_participant_{tournament_id}_{data['user_id']}"
            existing = await replit_db.get(participant_key)
            if existing:
                return web.json_response({'success': False, 'error': 'Already registered'})

            # Register participant
            participant_data = {
                'tournament_id': int(tournament_id),
                'user_id': data['user_id'],
                'age': data['age'],
                'phone_brand': data['phone_brand'],
                'nickname': data['nickname'],
                'game_id': data['game_id'],
                'registration_date': datetime.now().isoformat()
            }
            await replit_db.set(participant_key, participant_data)

            return web.json_response({'success': True})
        else:
            # SQLite version
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Check tournament status
                cursor = await db.execute('SELECT registration_status FROM tournaments WHERE id = ?', (tournament_id,))
                tournament = await cursor.fetchone()

                if not tournament:
                    return web.json_response({'success': False, 'error': 'Tournament not found'})

                status = tournament[0] if tournament[0] else 'open'
                if status == 'closed':
                    return web.json_response({'success': False, 'error': 'Registration is closed'})

                # Try to register
                await db.execute('''
                    INSERT INTO tournament_participants (tournament_id, user_id, age, phone_brand, nickname, game_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (tournament_id, data['user_id'], data['age'], data['phone_brand'], data['nickname'], data['game_id']))
                await db.commit()

            return web.json_response({'success': True})
    except Exception as e:
        print(f"❌ Tournament registration error: {e}")
        return web.json_response({'success': False, 'error': 'Already registered or other error'})

async def check_admin(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')

        print(f"🔍 Admin check request: user_id={user_id}")

        # Проверяем окружение - если это Replit/Preview, то включаем админку для всех
        is_preview = any(x in str(request.url) for x in ['repl.co', 'replit.dev', 'replit.app', '127.0.0.1', 'localhost'])

        print(f"🔧 Environment check: is_preview={is_preview}, URL={request.url}")

        if is_preview:
            is_admin = True
            print(f"✅ PREVIEW MODE: Granting admin access to user {user_id}")
        else:
            # В продакшене - только зарегистрированные админы
            is_admin = user_id in ADMIN_IDS if user_id else False
            print(f"🔒 PRODUCTION MODE: User {user_id} admin check: {is_admin} (ADMIN_IDS: {ADMIN_IDS})")

        response_data = {'is_admin': is_admin}
        print(f"📤 Returning admin check response: {response_data}")

        return web.json_response(response_data)
    except Exception as e:
        print(f"❌ Error in check_admin: {e}")
        # В случае ошибки - проверяем окружение
        is_preview = 'repl' in str(request.url) if hasattr(request, 'url') else True
        fallback_admin = is_preview
        print(f"🔧 Fallback admin access: {fallback_admin}")
        return web.json_response({'is_admin': fallback_admin})

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
    try:
        tournaments = await db_execute_query('''
            SELECT t.id, t.title, t.description, t.start_date, t.created_date, 
                   COALESCE(t.winners_count, 1) as winners_count, 
                   COALESCE(t.registration_status, 'open') as registration_status,
                   (SELECT COUNT(*) FROM tournament_participants tp WHERE tp.tournament_id = t.id) as participants
            FROM tournaments t
            GROUP BY t.id
            ORDER BY t.created_date DESC
        ''')

        result = []
        for row in tournaments:
            result.append({
                'id': row[0],
                'title': row[1],
                'description': row[2],
                'start_date': row[3],
                'created_date': row[4],
                'winners_count': row[5] if len(row) > 5 else 1,
                'registration_status': row[6] if len(row) > 6 else 'open',
                'participants': row[7] if len(row) > 7 else 0
            })

        return web.json_response(result)
    except Exception as e:
        print(f"Error loading tournaments: {e}")
        return web.json_response([])

async def get_tournament_participants(request):
    tournament_id = request.match_info['tournament_id']

    print(f"👥 Getting participants for tournament {tournament_id}")

    try:
        if USE_REPLIT_DB:
            # Get participants from Replit DB
            keys = await replit_db.list_keys(f"tournament_participant_{tournament_id}_")
            participants = []

            for key in keys:
                participant_data = await replit_db.get(key)
                if participant_data:
                    # Get user info
                    user_data = await replit_db.get(f"user_{participant_data['user_id']}")
                    if user_data:
                        participant_data.update({
                            'first_name': user_data.get('first_name'),
                            'username': user_data.get('username')
                        })
                    participants.append(participant_data)
        else:
            # Get participants from SQLite
            async with aiosqlite.connect(DATABASE_PATH) as db:
                cursor = await db.execute('''
                    SELECT tp.*, u.first_name, u.username
                    FROM tournament_participants tp
                    LEFT JOIN users u ON tp.user_id = u.user_id
                    WHERE tp.tournament_id = ?
                    ORDER BY tp.registration_date DESC
                ''', (tournament_id,))

                rows = await cursor.fetchall()
                participants = []

                for row in rows:
                    participants.append({
                        'id': row[0],
                        'tournament_id': row[1],
                        'user_id': row[2],
                        'age': row[3],
                        'phone_brand': row[4],
                        'nickname': row[5],
                        'game_id': row[6],
                        'registration_date': row[7],
                        'first_name': row[8] or 'Без имени',
                        'username': row[9]
                    })

        print(f"✅ Found {len(participants)} participants")
        return web.json_response(participants)

    except Exception as e:
        print(f"❌ Error getting tournament participants: {e}")
        return web.json_response([])


async def toggle_tournament_registration(request):
    try:
        tournament_id = int(request.match_info['tournament_id'])

        print(f"🔄 Toggling registration for tournament {tournament_id}")

        if USE_REPLIT_DB:
            # Handle Replit DB
            tournament_key = f"tournament_{tournament_id}"
            tournament = await replit_db.get(tournament_key)

            if not tournament:
                print(f"❌ Tournament {tournament_id} not found in Replit DB")
                return web.json_response({'success': False, 'error': 'Tournament not found'}, status=404)

            # Get current status
            current_status = tournament.get('registration_status', 'open')

            # Toggle logic
            if current_status == 'open':
                new_status = 'closed'
            else:
                new_status = 'open'

            print(f"📊 Replit DB - Changing {current_status} → {new_status}")

            # Update registration status
            tournament['registration_status'] = new_status
            await replit_db.set(tournament_key, tournament)

            print(f"✅ Replit DB - Tournament {tournament_id} registration updated to {new_status}")
            return web.json_response({'success': True, 'new_status': new_status, 'previous_status': current_status})

        else:
            # Handle SQLite
            async with aiosqlite.connect(DATABASE_PATH) as db:
                # Get current status
                cursor = await db.execute('SELECT registration_status FROM tournaments WHERE id = ?', (tournament_id,))
                row = await cursor.fetchone()

                if not row:
                    return web.json_response({'success': False, 'error': 'Турнир не найден'}, status=404)

                current_status = row[0] if row[0] else 'open'

                # Toggle logic
                if current_status == 'open':
                    new_status = 'closed'
                else:
                    new_status = 'open'

                print(f"📊 SQLite - Changing {current_status} → {new_status}")

                # Update status
                await db.execute(
                    'UPDATE tournaments SET registration_status = ? WHERE id = ?',
                    (new_status, tournament_id)
                )
                await db.commit()

                # Verify the update
                cursor = await db.execute('SELECT registration_status FROM tournaments WHERE id = ?', (tournament_id,))
                verify_row = await cursor.fetchone()
                actual_status = verify_row[0] if verify_row else 'unknown'

                print(f"✅ SQLite - Tournament {tournament_id} registration updated to {actual_status}")

                return web.json_response({'success': True, 'new_status': actual_status, 'previous_status': current_status})

    except Exception as e:
        print(f"❌ Error toggling tournament registration: {e}")
        import traceback
        traceback.print_exc()
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