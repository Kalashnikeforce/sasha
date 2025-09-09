
from aiohttp import web, ClientSession
import json
import os
import asyncio
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, WEB_APP_URL
import random
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import USE_POSTGRESQL, DATABASE_PUBLIC_URL
import asyncpg

# Database helper functions
async def db_execute_query(query, params=None):
    """Execute a query and return results"""
    if USE_POSTGRESQL:
        return await handle_postgresql_query(query, params)
    else:
        raise Exception("PostgreSQL not configured")

async def db_execute_update(query, params=None):
    """Execute an update query"""
    if USE_POSTGRESQL:
        return await handle_postgresql_update(query, params)
    else:
        raise Exception("PostgreSQL not configured")

async def handle_postgresql_query(query, params):
    """Handle SELECT queries for PostgreSQL"""
    try:
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        result = await conn.fetch(query, *(params or []))
        await conn.close()
        # Convert asyncpg records to list of dicts
        return [dict(record) for record in result]
    except Exception as e:
        print(f"PostgreSQL query error: {e}")
        return []

async def handle_postgresql_update(query, params):
    """Handle INSERT/UPDATE/DELETE queries for PostgreSQL"""
    try:
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        if 'RETURNING id' in query.upper():
            result = await conn.fetchval(query, *(params or []))
        else:
            await conn.execute(query, *(params or []))
            result = None
        await conn.close()
        return result
    except Exception as e:
        print(f"PostgreSQL update error: {e}")
        return None

async def index_handler(request):
    """Serve the main index.html file"""
    import os
    try:
        # Попробуем найти файл в static папке
        static_path = os.path.join(os.getcwd(), 'static', 'index.html')
        if os.path.exists(static_path):
            with open(static_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return web.Response(text=content, content_type='text/html')
        else:
            print(f"❌ index.html not found at: {static_path}")
            raise FileNotFoundError("index.html not found")
    except FileNotFoundError:
        return web.json_response({
            "message": "PUBG Bot Web App",
            "status": "running",
            "endpoints": ["/health", "/api/giveaways", "/api/tournaments"]
        })

async def health_handler(request):
    return web.json_response({"status": "ok", "message": "Bot is running"})

async def get_giveaways_handler(request):
    try:
        giveaways = await db_execute_query("SELECT * FROM giveaways ORDER BY created_date DESC")
        
        # Add participant count for each giveaway and fix datetime serialization
        for giveaway in giveaways:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = $1",
                [giveaway['id']]
            )
            giveaway['participants_count'] = participants[0]['count'] if participants else 0
            
            # Convert datetime objects to strings for JSON serialization
            if giveaway.get('created_date'):
                giveaway['created_date'] = giveaway['created_date'].isoformat() if hasattr(giveaway['created_date'], 'isoformat') else str(giveaway['created_date'])
            if giveaway.get('end_date'):
                giveaway['end_date'] = giveaway['end_date'].isoformat() if hasattr(giveaway['end_date'], 'isoformat') else str(giveaway['end_date'])
        
        return web.json_response(giveaways)
    except Exception as e:
        print(f"Error getting giveaways: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_tournaments_handler(request):
    try:
        tournaments = await db_execute_query("SELECT * FROM tournaments ORDER BY created_date DESC")
        
        # Add participant count for each tournament and fix datetime serialization
        for tournament in tournaments:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM tournament_participants WHERE tournament_id = $1",
                [tournament['id']]
            )
            tournament['participants_count'] = participants[0]['count'] if participants else 0
            
            # Convert datetime objects to strings for JSON serialization
            if tournament.get('created_date'):
                tournament['created_date'] = tournament['created_date'].isoformat() if hasattr(tournament['created_date'], 'isoformat') else str(tournament['created_date'])
        
        return web.json_response(tournaments)
    except Exception as e:
        print(f"Error getting tournaments: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_giveaway_handler(request):
    try:
        data = await request.json()
        
        print(f"🎁 Creating giveaway with data: {data}")
        
        # Validate required fields
        if not data.get('title'):
            return web.json_response({"error": "Название розыгрыша обязательно"}, status=400)
        
        # Parse end_date to datetime if provided
        end_date = None
        if data.get('end_date'):
            try:
                from datetime import datetime
                # Handle different date formats
                date_str = data['end_date']
                if 'T' not in date_str:
                    date_str += 'T00:00:00'
                end_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                print(f"📅 Parsed end_date: {end_date}")
            except Exception as date_error:
                print(f"Date parsing error: {date_error}")
                # Keep as string if parsing fails
                end_date = data['end_date']
        
        # Ensure winners_count is valid
        winners_count = 1
        try:
            winners_count = max(1, int(data.get('winners_count', 1)))
        except (ValueError, TypeError):
            winners_count = 1
        
        print(f"🎯 Creating giveaway: title={data['title']}, winners={winners_count}")
        
        giveaway_id = await db_execute_update('''
            INSERT INTO giveaways (title, description, end_date, winners_count, status)
            VALUES ($1, $2, $3, $4, $5) RETURNING id
        ''', [
            data['title'],
            data.get('description', ''),
            end_date,
            winners_count,
            'active'
        ])
        
        if giveaway_id:
            print(f"✅ Giveaway created with ID: {giveaway_id}")
            
            # Отправляем сообщение в канал
            try:
                await send_giveaway_to_channel(request.app['bot'], giveaway_id, data)
                print(f"✅ Giveaway {giveaway_id} sent to channel")
            except Exception as channel_error:
                print(f"⚠️ Error sending to channel: {channel_error}")
                # Don't fail the creation if channel sending fails
            
            return web.json_response({"success": True, "giveaway_id": giveaway_id})
        else:
            print("❌ Failed to create giveaway - no ID returned")
            return web.json_response({"error": "Failed to create giveaway"}, status=500)
            
    except Exception as e:
        print(f"❌ Error creating giveaway: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": f"Ошибка создания розыгрыша: {str(e)}"}, status=500)

async def create_tournament_handler(request):
    try:
        data = await request.json()
        
        tournament_id = await db_execute_update('''
            INSERT INTO tournaments (title, description, start_date, winners_count)
            VALUES ($1, $2, $3, $4) RETURNING id
        ''', [
            data['title'],
            data.get('description', ''),
            data.get('start_date', ''),  # Keep as string for tournaments
            data.get('winners_count', 1)
        ])
        
        if tournament_id:
            # Отправляем сообщение в канал
            await send_tournament_to_channel(request.app['bot'], tournament_id, data)
            
            return web.json_response({"success": True, "tournament_id": tournament_id})
        else:
            return web.json_response({"error": "Failed to create tournament"}, status=500)
            
    except Exception as e:
        print(f"Error creating tournament: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def delete_giveaway_handler(request):
    try:
        giveaway_id = int(request.match_info['giveaway_id'])
        
        await db_execute_update('DELETE FROM giveaways WHERE id = $1', [giveaway_id])
        
        return web.json_response({"success": True})
    except Exception as e:
        print(f"Error deleting giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def delete_tournament_handler(request):
    try:
        tournament_id = int(request.match_info['tournament_id'])
        
        await db_execute_update('DELETE FROM tournaments WHERE id = $1', [tournament_id])
        
        return web.json_response({"success": True})
    except Exception as e:
        print(f"Error deleting tournament: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_giveaway_participants_handler(request):
    try:
        giveaway_id = int(request.match_info['giveaway_id'])
        
        participants = await db_execute_query('''
            SELECT gp.user_id, u.username, u.first_name, u.last_name
            FROM giveaway_participants gp
            LEFT JOIN users u ON gp.user_id = u.user_id
            WHERE gp.giveaway_id = $1
        ''', [giveaway_id])
        
        return web.json_response(participants)
    except Exception as e:
        print(f"Error getting giveaway participants: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_tournament_participants_handler(request):
    try:
        tournament_id = int(request.match_info['tournament_id'])
        
        participants = await db_execute_query('''
            SELECT tp.*, u.username, u.first_name, u.last_name
            FROM tournament_participants tp
            LEFT JOIN users u ON tp.user_id = u.user_id
            WHERE tp.tournament_id = $1
        ''', [tournament_id])
        
        return web.json_response(participants)
    except Exception as e:
        print(f"Error getting tournament participants: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def draw_giveaway_winners_handler(request):
    try:
        giveaway_id = int(request.match_info['giveaway_id'])
        
        # Get giveaway info
        giveaway = await db_execute_query('SELECT * FROM giveaways WHERE id = $1', [giveaway_id])
        if not giveaway:
            return web.json_response({"error": "Giveaway not found"}, status=404)
        
        giveaway = giveaway[0]
        winners_count = giveaway['winners_count']
        
        # Get participants
        participants = await db_execute_query('''
            SELECT gp.user_id, u.username, u.first_name, u.last_name
            FROM giveaway_participants gp
            LEFT JOIN users u ON gp.user_id = u.user_id
            WHERE gp.giveaway_id = $1
        ''', [giveaway_id])
        
        if len(participants) == 0:
            return web.json_response({"error": "No participants found"}, status=400)
        
        # Select random winners
        winners = random.sample(participants, min(winners_count, len(participants)))
        
        # Save winners to database
        for i, winner in enumerate(winners):
            await db_execute_update('''
                INSERT INTO giveaway_winners (giveaway_id, user_id, place, name, username)
                VALUES ($1, $2, $3, $4, $5)
            ''', [
                giveaway_id,
                winner['user_id'],
                i + 1,
                f"{winner.get('first_name', '')} {winner.get('last_name', '')}".strip(),
                winner.get('username', '')
            ])
        
        # Update giveaway status
        await db_execute_update('UPDATE giveaways SET status = $1 WHERE id = $2', ['completed', giveaway_id])
        
        return web.json_response({"success": True, "winners": winners})
    except Exception as e:
        print(f"Error drawing winners: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def participate_giveaway_handler(request):
    """Handle giveaway participation from web app"""
    try:
        giveaway_id_str = request.match_info['giveaway_id']
        
        # Check if giveaway_id is valid
        if not giveaway_id_str or giveaway_id_str == 'None':
            return web.json_response({"error": "Неверный ID розыгрыша"}, status=400)
            
        try:
            giveaway_id = int(giveaway_id_str)
        except (ValueError, TypeError):
            return web.json_response({"error": "Неверный формат ID розыгрыша"}, status=400)
        
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({"error": "User ID is required"}, status=400)
        
        # Check if giveaway exists
        giveaway_check = await db_execute_query(
            'SELECT id FROM giveaways WHERE id = $1',
            [giveaway_id]
        )
        
        if not giveaway_check:
            return web.json_response({"error": "Розыгрыш не найден"}, status=404)
        
        # Check if user already participated
        existing = await db_execute_query(
            'SELECT id FROM giveaway_participants WHERE giveaway_id = $1 AND user_id = $2',
            [giveaway_id, user_id]
        )
        
        if existing:
            return web.json_response({"error": "Вы уже участвуете в этом розыгрыше!"}, status=400)
        
        # Add participant
        await db_execute_update(
            'INSERT INTO giveaway_participants (giveaway_id, user_id) VALUES ($1, $2)',
            [giveaway_id, user_id]
        )
        
        # Get updated participant count
        participant_count = await db_execute_query(
            'SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = $1',
            [giveaway_id]
        )
        count = participant_count[0]['count'] if participant_count and len(participant_count) > 0 else 0
        
        # Try to update the channel message button
        try:
            bot = request.app['bot']
            giveaway = await db_execute_query('SELECT * FROM giveaways WHERE id = $1', [giveaway_id])
            if giveaway and giveaway[0].get('message_id'):
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"🎮 Участвовать ({count})", 
                        callback_data=f"giveaway_participate_{giveaway_id}"
                    )]
                ])
                
                from config import CHANNEL_ID
                await bot.edit_message_reply_markup(
                    chat_id=CHANNEL_ID,
                    message_id=giveaway[0]['message_id'],
                    reply_markup=keyboard
                )
        except Exception as edit_error:
            print(f"Error updating channel message: {edit_error}")
        
        return web.json_response({
            "success": True, 
            "message": "Вы успешно зарегистрированы в розыгрыше!",
            "participants_count": count
        })
        
    except Exception as e:
        print(f"Error in giveaway participation: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def register_tournament_handler(request):
    """Handle tournament registration from web app"""
    try:
        tournament_id = int(request.match_info['tournament_id'])
        data = await request.json()
        
        user_id = data.get('user_id')
        age = data.get('age')
        phone_brand = data.get('phone_brand')
        nickname = data.get('nickname')
        game_id = data.get('game_id')
        
        if not all([user_id, age, phone_brand, nickname, game_id]):
            return web.json_response({"error": "Все поля обязательны для заполнения"}, status=400)
        
        # Check tournament status
        tournament = await db_execute_query(
            'SELECT status FROM tournaments WHERE id = $1',
            [tournament_id]
        )
        
        if not tournament:
            return web.json_response({"error": "Турнир не найден"}, status=404)
        
        if tournament[0]['status'] == 'closed':
            return web.json_response({"error": "Регистрация на турнир закрыта"}, status=400)
        
        # Check if user already registered
        existing = await db_execute_query(
            'SELECT id FROM tournament_participants WHERE tournament_id = $1 AND user_id = $2',
            [tournament_id, user_id]
        )
        
        if existing:
            return web.json_response({"error": "Вы уже зарегистрированы в этом турнире!"}, status=400)
        
        # Register participant
        await db_execute_update('''
            INSERT INTO tournament_participants (tournament_id, user_id, age, phone_brand, nickname, game_id)
            VALUES ($1, $2, $3, $4, $5, $6)
        ''', [tournament_id, user_id, age, phone_brand, nickname, game_id])
        
        return web.json_response({
            "success": True, 
            "message": "Вы успешно зарегистрированы в турнире!"
        })
        
    except Exception as e:
        print(f"Error in tournament registration: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def toggle_tournament_registration(request):
    """Toggle tournament registration status"""
    try:
        tournament_id = int(request.match_info['tournament_id'])
        data = await request.json()
        new_status = data.get('status', 'open')  # 'open' or 'closed'
        
        if new_status not in ['open', 'closed']:
            return web.json_response({"error": "Invalid status"}, status=400)
        
        # Update tournament status
        await db_execute_update(
            'UPDATE tournaments SET status = $1 WHERE id = $2',
            [new_status, tournament_id]
        )
        
        status_text = "открыта" if new_status == 'open' else "закрыта"
        
        return web.json_response({
            "success": True,
            "message": f"Регистрация {status_text}",
            "status": new_status
        })
        
    except Exception as e:
        print(f"Error toggling tournament registration: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def check_admin_status_handler(request):
    """Check if user is admin"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({"error": "User ID is required"}, status=400)
        
        is_admin = int(user_id) in ADMIN_IDS
        
        return web.json_response({
            "is_admin": is_admin,
            "admin_ids": ADMIN_IDS  # Отправляем список для отладки
        })
    except Exception as e:
        print(f"Error checking admin status: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_stats_handler(request):
    """Get admin statistics"""
    try:
        print("📊 Loading statistics...")
        
        # Получаем статистику пользователей
        try:
            users_count = await db_execute_query("SELECT COUNT(*) as count FROM users")
            users_total = users_count[0]['count'] if users_count and len(users_count) > 0 else 0
            print(f"👥 Users total: {users_total}")
        except Exception as e:
            print(f"Error getting users count: {e}")
            users_total = 0
        
        # Получаем статистику розыгрышей
        try:
            giveaways_count = await db_execute_query("SELECT COUNT(*) as count FROM giveaways")
            giveaways_total = giveaways_count[0]['count'] if giveaways_count and len(giveaways_count) > 0 else 0
            print(f"🎁 Giveaways total: {giveaways_total}")
        except Exception as e:
            print(f"Error getting giveaways count: {e}")
            giveaways_total = 0
        
        # Активные розыгрыши
        try:
            active_giveaways = await db_execute_query("SELECT COUNT(*) as count FROM giveaways WHERE status = 'active' OR status IS NULL")
            active_giveaways_count = active_giveaways[0]['count'] if active_giveaways and len(active_giveaways) > 0 else 0
            print(f"🎯 Active giveaways: {active_giveaways_count}")
        except Exception as e:
            print(f"Error getting active giveaways: {e}")
            active_giveaways_count = 0
        
        # Участники розыгрышей
        try:
            giveaway_participants = await db_execute_query("SELECT COUNT(*) as count FROM giveaway_participants")
            giveaway_participants_total = giveaway_participants[0]['count'] if giveaway_participants and len(giveaway_participants) > 0 else 0
            print(f"🎮 Giveaway participants: {giveaway_participants_total}")
        except Exception as e:
            print(f"Error getting giveaway participants: {e}")
            giveaway_participants_total = 0
        
        # Получаем статистику турниров
        try:
            tournaments_count = await db_execute_query("SELECT COUNT(*) as count FROM tournaments")
            tournaments_total = tournaments_count[0]['count'] if tournaments_count and len(tournaments_count) > 0 else 0
            print(f"🏆 Tournaments total: {tournaments_total}")
        except Exception as e:
            print(f"Error getting tournaments count: {e}")
            tournaments_total = 0
        
        # Активные турниры
        try:
            active_tournaments = await db_execute_query("SELECT COUNT(*) as count FROM tournaments WHERE status = 'open' OR status IS NULL")
            active_tournaments_count = active_tournaments[0]['count'] if active_tournaments and len(active_tournaments) > 0 else 0
            print(f"⚡ Active tournaments: {active_tournaments_count}")
        except Exception as e:
            print(f"Error getting active tournaments: {e}")
            active_tournaments_count = 0
        
        # Участники турниров
        try:
            tournament_participants = await db_execute_query("SELECT COUNT(*) as count FROM tournament_participants")
            tournament_participants_total = tournament_participants[0]['count'] if tournament_participants and len(tournament_participants) > 0 else 0
            print(f"🎯 Tournament participants: {tournament_participants_total}")
        except Exception as e:
            print(f"Error getting tournament participants: {e}")
            tournament_participants_total = 0
        
        stats = {
            "users": users_total,
            "giveaways": giveaways_total,
            "active_giveaways": active_giveaways_count,
            "giveaway_participants": giveaway_participants_total,
            "tournaments": tournaments_total,
            "active_tournaments": active_tournaments_count,
            "tournament_participants": tournament_participants_total
        }
        
        print(f"📊 Final stats: {stats}")
        return web.json_response(stats)
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({
            "users": 0,
            "giveaways": 0,
            "active_giveaways": 0,
            "giveaway_participants": 0,
            "tournaments": 0,
            "active_tournaments": 0,
            "tournament_participants": 0,
            "error": str(e)
        }, status=200)

async def check_subscription_handler(request):
    """Check if user is subscribed to channel"""
    try:
        data = await request.json()
        user_id = data.get('user_id')
        
        if not user_id:
            return web.json_response({"error": "User ID is required"}, status=400)
        
        # Пока что возвращаем True, так как проверка подписки требует дополнительной настройки
        # В будущем здесь будет реальная проверка через Bot API
        return web.json_response({"is_subscribed": True})
        
    except Exception as e:
        print(f"Error checking subscription: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def send_giveaway_to_channel(bot, giveaway_id, data):
    """Send giveaway message to channel"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from config import CHANNEL_ID
        
        # Формируем текст сообщения
        title = data['title']
        description = data.get('description', '')
        end_date = data.get('end_date', '')
        winners_count = data.get('winners_count', 1)
        
        # Форматируем дату
        formatted_date = ""
        if end_date:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                formatted_date = f"\n⏰ <b>Дата окончания:</b> {dt.strftime('%d.%m.%Y в %H:%M')}"
            except:
                formatted_date = f"\n⏰ <b>Дата окончания:</b> {end_date}"
        
        message_text = f"""🎁 <b>НОВЫЙ РОЗЫГРЫШ!</b>
        
🎯 <b>{title}</b>

📝 <b>Описание:</b>
{description}{formatted_date}

🏆 <b>Количество победителей:</b> {winners_count}

🎮 Для участия нажмите кнопку ниже!
"""
        
        # Создаем кнопку участия
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=f"🎮 Участвовать (0)", 
                callback_data=f"giveaway_participate_{giveaway_id}"
            )]
        ])
        
        # Отправляем сообщение в канал
        sent_message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Сохраняем ID сообщения в базу данных
        await db_execute_update(
            'UPDATE giveaways SET message_id = $1 WHERE id = $2',
            [sent_message.message_id, giveaway_id]
        )
        
        print(f"✅ Giveaway {giveaway_id} sent to channel with message ID {sent_message.message_id}")
        
    except Exception as e:
        print(f"❌ Error sending giveaway to channel: {e}")

async def send_tournament_to_channel(bot, tournament_id, data):
    """Send tournament message to channel"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        from config import CHANNEL_ID, WEB_APP_URL
        
        # Формируем текст сообщения
        title = data['title']
        description = data.get('description', '')
        start_date = data.get('start_date', '')
        winners_count = data.get('winners_count', 1)
        
        # Форматируем дату
        formatted_date = ""
        if start_date:
            formatted_date = f"\n🚀 <b>Дата начала:</b> {start_date}"
        
        message_text = f"""🏆 <b>НОВЫЙ ТУРНИР!</b>
        
🎯 <b>{title}</b>

📝 <b>Описание:</b>
{description}{formatted_date}

🥇 <b>Количество призовых мест:</b> {winners_count}

⚡ Для регистрации используйте команду /start и выберите турнир!
"""
        
        # Создаем кнопку регистрации
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🏆 Зарегистрироваться", 
                url=f"https://t.me/{(await bot.get_me()).username}?start=tournament_{tournament_id}"
            )]
        ])
        
        # Отправляем сообщение в канал
        sent_message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
        # Сохраняем ID сообщения в базу данных
        await db_execute_update(
            'UPDATE tournaments SET message_id = $1 WHERE id = $2',
            [sent_message.message_id, tournament_id]
        )
        
        print(f"✅ Tournament {tournament_id} sent to channel with message ID {sent_message.message_id}")
        
    except Exception as e:
        print(f"❌ Error sending tournament to channel: {e}")

async def create_app(bot):
    app = web.Application()
    
    # Store bot instance in app for handlers
    app['bot'] = bot
    
    # Routes
    app.router.add_get('/', index_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_post('/api/check-admin', check_admin_status_handler)
    
    # API routes
    app.router.add_post('/api/check-subscription', check_subscription_handler)
    app.router.add_get('/api/stats', get_stats_handler)
    app.router.add_get('/api/giveaways', get_giveaways_handler)
    app.router.add_get('/api/tournaments', get_tournaments_handler)
    app.router.add_post('/api/giveaways', create_giveaway_handler)
    app.router.add_post('/api/tournaments', create_tournament_handler)
    app.router.add_delete('/api/giveaways/{giveaway_id}', delete_giveaway_handler)
    app.router.add_delete('/api/tournaments/{tournament_id}', delete_tournament_handler)
    app.router.add_get('/api/giveaways/{giveaway_id}/participants', get_giveaway_participants_handler)
    app.router.add_get('/api/tournaments/{tournament_id}/participants', get_tournament_participants_handler)
    app.router.add_post('/api/giveaways/{giveaway_id}/draw', draw_giveaway_winners_handler)
    app.router.add_post('/api/giveaways/{giveaway_id}/participate', participate_giveaway_handler)
    app.router.add_post('/api/tournaments/{tournament_id}/register', register_tournament_handler)
    app.router.add_post('/api/tournaments/{tournament_id}/toggle-registration', toggle_tournament_registration)
    
    # Static files
    app.router.add_static('/static', 'static', name='static')
    
    return app
