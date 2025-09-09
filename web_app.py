
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
        # Get all giveaways with participant count in one query
        giveaways = await db_execute_query("""
            SELECT g.*, 
                   COALESCE(p.participant_count, 0) as participants
            FROM giveaways g
            LEFT JOIN (
                SELECT giveaway_id, COUNT(*) as participant_count 
                FROM giveaway_participants 
                GROUP BY giveaway_id
            ) p ON g.id = p.giveaway_id
            ORDER BY g.created_date DESC
        """)
        
        # Fix datetime serialization
        for giveaway in giveaways:
            # Convert datetime objects to strings for JSON serialization
            if giveaway.get('created_date'):
                giveaway['created_date'] = giveaway['created_date'].isoformat() if hasattr(giveaway['created_date'], 'isoformat') else str(giveaway['created_date'])
            if giveaway.get('end_date'):
                giveaway['end_date'] = giveaway['end_date'].isoformat() if hasattr(giveaway['end_date'], 'isoformat') else str(giveaway['end_date'])
        
        print(f"📋 Loaded {len(giveaways)} giveaways")
        return web.json_response(giveaways)
        
    except Exception as e:
        print(f"❌ Error getting giveaways: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def get_tournaments_handler(request):
    try:
        # Get all tournaments with participant count in one query
        tournaments = await db_execute_query("""
            SELECT t.*, 
                   COALESCE(p.participant_count, 0) as participants
            FROM tournaments t
            LEFT JOIN (
                SELECT tournament_id, COUNT(*) as participant_count 
                FROM tournament_participants 
                GROUP BY tournament_id
            ) p ON t.id = p.tournament_id
            ORDER BY t.created_date DESC
        """)
        
        # Fix datetime serialization and ensure all fields are present
        for tournament in tournaments:
            # Convert datetime objects to strings for JSON serialization
            if tournament.get('created_date'):
                tournament['created_date'] = tournament['created_date'].isoformat() if hasattr(tournament['created_date'], 'isoformat') else str(tournament['created_date'])
            
            # Ensure registration_status field exists
            if not tournament.get('registration_status'):
                tournament['registration_status'] = tournament.get('status', 'open')
        
        print(f"🏆 Loaded {len(tournaments)} tournaments")
        return web.json_response(tournaments)
        
    except Exception as e:
        print(f"❌ Error getting tournaments: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def create_giveaway_handler(request):
    try:
        data = await request.json()
        
        print(f"🎁 Creating giveaway with data: {data}")
        
        # Validate required fields
        if not data.get('title'):
            return web.json_response({"error": "Название розыгрыша обязательно"}, status=400)
        
        # Parse end_date to proper datetime for PostgreSQL
        end_date = None
        if data.get('end_date'):
            try:
                from datetime import datetime
                # Handle different date formats
                date_str = data['end_date']
                if 'T' not in date_str:
                    date_str += 'T00:00:00'
                end_date = datetime.fromisoformat(date_str.replace('Z', ''))
                print(f"📅 Parsed end_date: {end_date}")
            except Exception as date_error:
                print(f"⚠️ Date parsing error: {date_error}")
                # Set to None if parsing fails
                end_date = None
        
        # Ensure winners_count is valid
        winners_count = 1
        try:
            winners_count = max(1, int(data.get('winners_count', 1)))
        except (ValueError, TypeError):
            winners_count = 1
        
        print(f"🎯 Creating giveaway: title={data['title']}, winners={winners_count}, end_date={end_date}")
        
        # Use proper PostgreSQL INSERT with RETURNING
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        giveaway_id = await conn.fetchval('''
            INSERT INTO giveaways (title, description, end_date, winners_count, status, created_date)
            VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP) RETURNING id
        ''', data['title'], data.get('description', ''), end_date, winners_count, 'active')
        await conn.close()
        
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
        
        print(f"🏆 Creating tournament with data: {data}")
        
        # Validate required fields
        if not data.get('title'):
            return web.json_response({"error": "Название турнира обязательно"}, status=400)
        
        # Get registration status
        registration_open = data.get('registration_open', True)
        status = 'open' if registration_open else 'closed'
        
        # Use direct PostgreSQL connection for better error handling
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        tournament_id = await conn.fetchval('''
            INSERT INTO tournaments (title, description, start_date, winners_count, status, registration_status, created_date)
            VALUES ($1, $2, $3, $4, $5, $6, CURRENT_TIMESTAMP) RETURNING id
        ''', data['title'], data.get('description', ''), data.get('start_date', ''), data.get('winners_count', 1), status, status)
        await conn.close()
        
        if tournament_id:
            print(f"✅ Tournament created with ID: {tournament_id}")
            
            # Отправляем сообщение в канал
            try:
                await send_tournament_to_channel(request.app['bot'], tournament_id, data)
                print(f"✅ Tournament {tournament_id} sent to channel")
            except Exception as channel_error:
                print(f"⚠️ Error sending tournament to channel: {channel_error}")
            
            return web.json_response({"success": True, "tournament_id": tournament_id})
        else:
            print("❌ Failed to create tournament - no ID returned")
            return web.json_response({"error": "Failed to create tournament"}, status=500)
            
    except Exception as e:
        print(f"❌ Error creating tournament: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def delete_giveaway_handler(request):
    try:
        giveaway_id = int(request.match_info['giveaway_id'])
        
        # Используем транзакцию для удаления всех связанных записей
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            async with conn.transaction():
                # Удаляем участников розыгрыша
                await conn.execute('DELETE FROM giveaway_participants WHERE giveaway_id = $1', giveaway_id)
                
                # Удаляем победителей розыгрыша
                await conn.execute('DELETE FROM giveaway_winners WHERE giveaway_id = $1', giveaway_id)
                
                # Удаляем призы розыгрыша
                await conn.execute('DELETE FROM giveaway_prizes WHERE giveaway_id = $1', giveaway_id)
                
                # Удаляем сам розыгрыш
                await conn.execute('DELETE FROM giveaways WHERE id = $1', giveaway_id)
                
                print(f"✅ Giveaway {giveaway_id} and all related data deleted successfully")
                
        finally:
            await conn.close()
        
        return web.json_response({"success": True})
    except Exception as e:
        print(f"❌ Error deleting giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def delete_tournament_handler(request):
    try:
        tournament_id = int(request.match_info['tournament_id'])
        
        # Используем транзакцию для удаления всех связанных записей
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            async with conn.transaction():
                # Удаляем участников турнира
                await conn.execute('DELETE FROM tournament_participants WHERE tournament_id = $1', tournament_id)
                
                # Удаляем сам турнир
                await conn.execute('DELETE FROM tournaments WHERE id = $1', tournament_id)
                
                print(f"✅ Tournament {tournament_id} and all related data deleted successfully")
                
        finally:
            await conn.close()
        
        return web.json_response({"success": True})
    except Exception as e:
        print(f"❌ Error deleting tournament: {e}")
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
        
        # Use direct PostgreSQL connection for transaction
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            # Ensure all winner users exist in users table
            for winner in winners:
                await conn.execute('''
                    INSERT INTO users (user_id, username, first_name, last_name, is_subscribed) 
                    VALUES ($1, $2, $3, $4, TRUE) 
                    ON CONFLICT (user_id) DO UPDATE SET
                        username = $2,
                        first_name = $3,
                        last_name = $4,
                        is_subscribed = TRUE
                ''', 
                winner['user_id'], 
                winner.get('username', ''), 
                winner.get('first_name', ''), 
                winner.get('last_name', ''))
            
            # Save winners to database
            for i, winner in enumerate(winners):
                await conn.execute('''
                    INSERT INTO giveaway_winners (giveaway_id, user_id, place, name, username)
                    VALUES ($1, $2, $3, $4, $5)
                ''', 
                giveaway_id,
                winner['user_id'],
                i + 1,
                f"{winner.get('first_name', '') or ''} {winner.get('last_name', '') or ''}".strip() or f"User {winner['user_id']}",
                winner.get('username', ''))
            
            # Update giveaway status
            await conn.execute('UPDATE giveaways SET status = $1 WHERE id = $2', 'completed', giveaway_id)
            
        finally:
            await conn.close()
        
        # Send winners announcement to channel
        try:
            await send_winners_to_channel(request.app['bot'], giveaway_id, giveaway, winners)
            print(f"✅ Winners announced in channel for giveaway {giveaway_id}")
        except Exception as channel_error:
            print(f"⚠️ Error sending winners to channel: {channel_error}")
        
        return web.json_response({"success": True, "winners": winners})
        
    except Exception as e:
        print(f"❌ Error drawing winners: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": str(e)}, status=500)

async def participate_giveaway_handler(request):
    """Handle giveaway participation from web app"""
    try:
        giveaway_id_str = request.match_info['giveaway_id']
        
        print(f"🎮 Participation request for giveaway: {giveaway_id_str}")
        
        # Check if giveaway_id is valid
        if not giveaway_id_str or giveaway_id_str == 'None' or giveaway_id_str == 'undefined':
            print(f"❌ Invalid giveaway ID: {giveaway_id_str}")
            return web.json_response({"error": "Неверный ID розыгрыша"}, status=400)
            
        try:
            giveaway_id = int(giveaway_id_str)
        except (ValueError, TypeError):
            print(f"❌ Invalid giveaway ID format: {giveaway_id_str}")
            return web.json_response({"error": "Неверный формат ID розыгрыша"}, status=400)
        
        data = await request.json()
        user_id = data.get('user_id')
        
        print(f"👤 User ID: {user_id}")
        
        if not user_id:
            return web.json_response({"error": "User ID is required"}, status=400)
        
        # Use direct PostgreSQL connection for better control
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            # Check if giveaway exists and is active
            giveaway = await conn.fetchrow('SELECT id, status FROM giveaways WHERE id = $1', giveaway_id)
            
            if not giveaway:
                return web.json_response({"error": "Розыгрыш не найден"}, status=404)
            
            if giveaway['status'] == 'completed':
                return web.json_response({"error": "Розыгрыш уже завершен"}, status=400)
            
            # Check if user already participated
            existing = await conn.fetchrow(
                'SELECT id FROM giveaway_participants WHERE giveaway_id = $1 AND user_id = $2',
                giveaway_id, user_id
            )
            
            if existing:
                return web.json_response({"error": "Вы уже участвуете в этом розыгрыше!"}, status=400)
            
            # Add user to users table if not exists
            await conn.execute('''
                INSERT INTO users (user_id, first_name) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO NOTHING
            ''', user_id, f"User {user_id}")
            
            # Add participant
            await conn.execute(
                'INSERT INTO giveaway_participants (giveaway_id, user_id) VALUES ($1, $2)',
                giveaway_id, user_id
            )
            
            # Get updated participant count
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM giveaway_participants WHERE giveaway_id = $1',
                giveaway_id
            )
            
            print(f"✅ User {user_id} added to giveaway {giveaway_id}. Total participants: {count}")
            
        finally:
            await conn.close()
        
        # Try to update the channel message button
        try:
            bot = request.app['bot']
            giveaway_info = await db_execute_query('SELECT message_id FROM giveaways WHERE id = $1', [giveaway_id])
            
            if giveaway_info and giveaway_info[0].get('message_id'):
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
                    message_id=giveaway_info[0]['message_id'],
                    reply_markup=keyboard
                )
                print(f"✅ Updated channel message button with count: {count}")
                
        except Exception as edit_error:
            print(f"⚠️ Error updating channel message: {edit_error}")
        
        return web.json_response({
            "success": True, 
            "message": "Вы успешно зарегистрированы в розыгрыше!",
            "participants_count": count
        })
        
    except Exception as e:
        print(f"❌ Error in giveaway participation: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": f"Ошибка регистрации: {str(e)}"}, status=500)

async def register_tournament_handler(request):
    """Handle tournament registration from web app"""
    try:
        tournament_id_str = request.match_info['tournament_id']
        
        print(f"🏆 Tournament registration request for tournament: {tournament_id_str}")
        
        # Check if tournament_id is valid
        if not tournament_id_str or tournament_id_str == 'None' or tournament_id_str == 'undefined':
            print(f"❌ Invalid tournament ID: {tournament_id_str}")
            return web.json_response({"error": "Неверный ID турнира"}, status=400)
            
        try:
            tournament_id = int(tournament_id_str)
        except (ValueError, TypeError):
            print(f"❌ Invalid tournament ID format: {tournament_id_str}")
            return web.json_response({"error": "Неверный формат ID турнира"}, status=400)
        
        data = await request.json()
        
        user_id = data.get('user_id')
        age = data.get('age')
        phone_brand = data.get('phone_brand')
        nickname = data.get('nickname')
        game_id = data.get('game_id')
        
        print(f"👤 Registration data: user_id={user_id}, age={age}, nickname={nickname}")
        
        if not all([user_id, age, phone_brand, nickname, game_id]):
            return web.json_response({"error": "Все поля обязательны для заполнения"}, status=400)
        
        # Use direct PostgreSQL connection for better control
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            # Check if tournament exists and get its status
            tournament = await conn.fetchrow(
                'SELECT id, status, registration_status FROM tournaments WHERE id = $1',
                tournament_id
            )
            
            if not tournament:
                return web.json_response({"error": "Турнир не найден"}, status=404)
            
            # Check registration status (используем registration_status или status)
            reg_status = tournament.get('registration_status') or tournament.get('status', 'open')
            if reg_status == 'closed':
                return web.json_response({"error": "Регистрация на турнир закрыта"}, status=400)
            
            # Check if user already registered
            existing = await conn.fetchrow(
                'SELECT id FROM tournament_participants WHERE tournament_id = $1 AND user_id = $2',
                tournament_id, user_id
            )
            
            if existing:
                return web.json_response({"error": "Вы уже зарегистрированы в этом турнире!"}, status=400)
            
            # Add user to users table if not exists (важно для foreign key)
            await conn.execute('''
                INSERT INTO users (user_id, first_name) 
                VALUES ($1, $2) 
                ON CONFLICT (user_id) DO NOTHING
            ''', user_id, f"User {user_id}")
            
            # Register participant
            await conn.execute('''
                INSERT INTO tournament_participants (tournament_id, user_id, age, phone_brand, nickname, game_id)
                VALUES ($1, $2, $3, $4, $5, $6)
            ''', tournament_id, user_id, age, phone_brand, nickname, game_id)
            
            # Get updated participant count
            count = await conn.fetchval(
                'SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = $1',
                tournament_id
            )
            
            print(f"✅ User {user_id} registered for tournament {tournament_id}. Total participants: {count}")
            
        finally:
            await conn.close()
        
        # Try to update the channel message if exists
        try:
            bot = request.app['bot']
            tournament_info = await db_execute_query('SELECT message_id FROM tournaments WHERE id = $1', [tournament_id])
            
            if tournament_info and tournament_info[0].get('message_id'):
                from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(
                        text=f"🏆 Участники ({count})", 
                        url=f"https://t.me/{(await bot.get_me()).username}?start=tournament_{tournament_id}"
                    )]
                ])
                
                from config import CHANNEL_ID
                await bot.edit_message_reply_markup(
                    chat_id=CHANNEL_ID,
                    message_id=tournament_info[0]['message_id'],
                    reply_markup=keyboard
                )
                print(f"✅ Updated tournament channel message with count: {count}")
                
        except Exception as edit_error:
            print(f"⚠️ Error updating tournament channel message: {edit_error}")
        
        return web.json_response({
            "success": True, 
            "message": "Вы успешно зарегистрированы в турнире!",
            "participants_count": count
        })
        
    except Exception as e:
        print(f"❌ Error in tournament registration: {e}")
        import traceback
        traceback.print_exc()
        return web.json_response({"error": f"Ошибка регистрации: {str(e)}"}, status=500)

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
        
        stats = {
            "total_users": 0,
            "active_users": 0,
            "total_giveaways": 0,
            "active_giveaways": 0,
            "giveaway_participants": 0,
            "total_tournaments": 0,
            "active_tournaments": 0,
            "tournament_participants": 0
        }
        
        # Use direct PostgreSQL connection for reliable stats
        conn = await asyncpg.connect(DATABASE_PUBLIC_URL)
        
        try:
            # Users statistics
            stats["total_users"] = await conn.fetchval("SELECT COUNT(*) FROM users") or 0
            stats["active_users"] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_subscribed = TRUE") or 0
            
            # Giveaways statistics
            stats["total_giveaways"] = await conn.fetchval("SELECT COUNT(*) FROM giveaways") or 0
            stats["active_giveaways"] = await conn.fetchval("SELECT COUNT(*) FROM giveaways WHERE status = 'active' OR status IS NULL") or 0
            stats["giveaway_participants"] = await conn.fetchval("SELECT COUNT(*) FROM giveaway_participants") or 0
            
            # Tournaments statistics
            stats["total_tournaments"] = await conn.fetchval("SELECT COUNT(*) FROM tournaments") or 0
            stats["active_tournaments"] = await conn.fetchval("SELECT COUNT(*) FROM tournaments WHERE status = 'open' OR status IS NULL") or 0
            stats["tournament_participants"] = await conn.fetchval("SELECT COUNT(*) FROM tournament_participants") or 0
            
        finally:
            await conn.close()
        
        print(f"📊 Stats loaded: {stats}")
        return web.json_response(stats)
        
    except Exception as e:
        print(f"❌ Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        
        # Return zero stats on error
        return web.json_response({
            "total_users": 0,
            "active_users": 0,
            "total_giveaways": 0,
            "active_giveaways": 0,
            "giveaway_participants": 0,
            "total_tournaments": 0,
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

async def send_winners_to_channel(bot, giveaway_id, giveaway, winners):
    """Send giveaway winners announcement to channel"""
    try:
        from config import CHANNEL_ID
        
        # Формируем текст с победителями
        winners_text = ""
        for i, winner in enumerate(winners):
            place_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}️⃣"
            username = winner.get('username', '')
            name = f"{winner.get('first_name', '') or ''} {winner.get('last_name', '') or ''}".strip()
            
            if username:
                winner_mention = f"@{username}"
            elif name and name != f"User {winner['user_id']}":
                winner_mention = name
            else:
                winner_mention = f"User ID: {winner['user_id']}"
                
            winners_text += f"{place_emoji} {winner_mention}\n"
        
        message_text = f"""🎉 <b>РЕЗУЛЬТАТЫ РОЗЫГРЫША!</b>

🎯 <b>{giveaway['title']}</b>

🏆 <b>Победители:</b>
{winners_text}

🎊 Поздравляем победителей! Ожидайте связи с администратором для получения приза.
"""
        
        # Отправляем сообщение о победителях
        await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            parse_mode='HTML'
        )
        
        print(f"✅ Winners announcement sent for giveaway {giveaway_id}")
        
    except Exception as e:
        print(f"❌ Error sending winners announcement: {e}")

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
