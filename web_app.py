from aiohttp import web, ClientSession
import json
import os
import asyncio
from config import BOT_TOKEN, CHANNEL_ID, ADMIN_IDS, WEB_APP_URL
import random
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import USE_REPLIT_DB, replit_db, USE_POSTGRESQL, DATABASE_PUBLIC_URL
import asyncpg

# Database helper functions
async def db_execute_query(query, params=None):
    """Execute a query and return results"""
    if USE_POSTGRESQL:
        return await handle_postgresql_query(query, params)
    elif USE_REPLIT_DB:
        return await handle_replit_db_query(query, params)
    else:
        raise Exception("No database configured")

async def db_execute_update(query, params=None):
    """Execute an update query"""
    if USE_POSTGRESQL:
        return await handle_postgresql_update(query, params)
    elif USE_REPLIT_DB:
        return await handle_replit_db_update(query, params)
    else:
        raise Exception("No database configured")

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

async def handle_replit_db_query(query, params):
    """Handle SELECT queries for Replit DB"""
    query_lower = query.lower().strip()

    if 'select * from giveaways' in query_lower:
        # Get all giveaways
        keys = await replit_db.list_keys("giveaway_")
        giveaways = []
        for key in keys:
            if not key.startswith("giveaway_participant_"):
                data = await replit_db.get(key)
                if data:
                    giveaways.append(data)
        return giveaways

    elif 'select * from tournaments' in query_lower:
        # Get all tournaments
        keys = await replit_db.list_keys("tournament_")
        tournaments = []
        for key in keys:
            if not key.startswith("tournament_participant_"):
                data = await replit_db.get(key)
                if data:
                    tournaments.append(data)
        return tournaments

    elif 'count(*) from giveaway_participants' in query_lower:
        # Count participants for a specific giveaway
        if params and len(params) > 0:
            giveaway_id = params[0]
            keys = await replit_db.list_keys(f"giveaway_participant_{giveaway_id}_")
            return [{'count': len(keys)}]
        return [{'count': 0}]

    elif 'count(*) from tournament_participants' in query_lower:
        # Count participants for a specific tournament
        if params and len(params) > 0:
            tournament_id = params[0]
            keys = await replit_db.list_keys(f"tournament_participant_{tournament_id}_")
            return [{'count': len(keys)}]
        return [{'count': 0}]

    elif 'select * from tournament_participants' in query_lower:
        # Get tournament participants
        if params and len(params) > 0:
            tournament_id = params[0]
            keys = await replit_db.list_keys(f"tournament_participant_{tournament_id}_")
            participants = []
            for key in keys:
                data = await replit_db.get(key)
                if data:
                    participants.append(data)
            return participants
        return []

    return []

async def handle_replit_db_update(query, params):
    """Handle INSERT/UPDATE/DELETE queries for Replit DB"""
    query_lower = query.lower().strip()

    if 'insert into giveaways' in query_lower:
        # Create new giveaway
        if params and len(params) >= 2:
            giveaway_id = random.randint(1000, 9999)
            giveaway_data = {
                'id': giveaway_id,
                'title': params[0],
                'description': params[1],
                'end_date': params[2] if len(params) > 2 else None,
                'is_active': True,
                'created_date': datetime.now().isoformat(),
                'winners_count': params[3] if len(params) > 3 else 1,
                'status': 'active'
            }
            await replit_db.set(f"giveaway_{giveaway_id}", giveaway_data)
            return giveaway_id

    elif 'insert into tournaments' in query_lower:
        # Create new tournament
        if params and len(params) >= 2:
            tournament_id = random.randint(1000, 9999)
            tournament_data = {
                'id': tournament_id,
                'title': params[0],
                'description': params[1],
                'start_date': params[2] if len(params) > 2 else None,
                'created_date': datetime.now().isoformat(),
                'winners_count': params[3] if len(params) > 3 else 1,
                'registration_status': 'open'
            }
            await replit_db.set(f"tournament_{tournament_id}", tournament_data)
            return tournament_id

    elif 'update giveaways set status' in query_lower:
        # Update giveaway status
        if params and len(params) >= 2:
            status = params[0]
            giveaway_id = params[1]
            giveaway_data = await replit_db.get(f"giveaway_{giveaway_id}")
            if giveaway_data:
                giveaway_data['status'] = status
                await replit_db.set(f"giveaway_{giveaway_id}", giveaway_data)
            return giveaway_id

    elif 'update tournaments set registration_status' in query_lower:
        # Update tournament registration status
        if params and len(params) >= 2:
            status = params[0]
            tournament_id = params[1]
            tournament_data = await replit_db.get(f"tournament_{tournament_id}")
            if tournament_data:
                tournament_data['registration_status'] = status
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

async def health_handler(request):
    return web.json_response({"status": "ok", "message": "Bot is running"})

async def get_giveaways_handler(request):
    try:
        giveaways = await db_execute_query("SELECT * FROM giveaways ORDER BY created_date DESC")

        # Add participant count to each giveaway
        for giveaway in giveaways:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = ?",
                [giveaway['id']]
            )
            giveaway['participant_count'] = participants[0]['count'] if participants else 0

        return web.json_response(giveaways)
    except Exception as e:
        print(f"Error getting giveaways: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_tournaments_handler(request):
    try:
        tournaments = await db_execute_query("SELECT * FROM tournaments ORDER BY created_date DESC")

        # Add participant count to each tournament
        for tournament in tournaments:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM tournament_participants WHERE tournament_id = ?",
                [tournament['id']]
            )
            tournament['participant_count'] = participants[0]['count'] if participants else 0

        return web.json_response(tournaments)
    except Exception as e:
        print(f"Error getting tournaments: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_giveaway_handler(request):
    try:
        data = await request.json()
        title = data.get('title')
        description = data.get('description')
        end_date = data.get('end_date')
        winners_count = data.get('winners_count', 1)

        if not title:
            return web.json_response({"error": "Title is required"}, status=400)

        giveaway_id = await db_execute_update(
            "INSERT INTO giveaways (title, description, end_date, winners_count) VALUES (?, ?, ?, ?)",
            [title, description, end_date, winners_count]
        )

        return web.json_response({"id": giveaway_id, "message": "Giveaway created successfully"})
    except Exception as e:
        print(f"Error creating giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_tournament_handler(request):
    try:
        data = await request.json()
        title = data.get('title')
        description = data.get('description')
        start_date = data.get('start_date')
        winners_count = data.get('winners_count', 1)

        if not title:
            return web.json_response({"error": "Title is required"}, status=400)

        tournament_id = await db_execute_update(
            "INSERT INTO tournaments (title, description, start_date, winners_count) VALUES (?, ?, ?, ?)",
            [title, description, start_date, winners_count]
        )

        return web.json_response({"id": tournament_id, "message": "Tournament created successfully"})
    except Exception as e:
        print(f"Error creating tournament: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def finish_giveaway_handler(request):
    try:
        giveaway_id = int(request.match_info['id'])

        # Update giveaway status to finished
        await db_execute_update(
            "UPDATE giveaways SET status = ? WHERE id = ?",
            ['finished', giveaway_id]
        )

        return web.json_response({"message": "Giveaway finished successfully"})
    except Exception as e:
        print(f"Error finishing giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def close_tournament_handler(request):
    try:
        tournament_id = int(request.match_info['id'])

        # Update tournament registration status to closed
        await db_execute_update(
            "UPDATE tournaments SET registration_status = ? WHERE id = ?",
            ['closed', tournament_id]
        )

        return web.json_response({"message": "Tournament registration closed successfully"})
    except Exception as e:
        print(f"Error closing tournament: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def delete_giveaway_handler(request):
    try:
        giveaway_id = int(request.match_info['id'])

        await db_execute_update("DELETE FROM giveaways WHERE id = ?", [giveaway_id])

        return web.json_response({"message": "Giveaway deleted successfully"})
    except Exception as e:
        print(f"Error deleting giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def delete_tournament_handler(request):
    try:
        tournament_id = int(request.match_info['id'])

        await db_execute_update("DELETE FROM tournaments WHERE id = ?", [tournament_id])

        return web.json_response({"message": "Tournament deleted successfully"})
    except Exception as e:
        print(f"Error deleting tournament: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_tournament_participants_handler(request):
    try:
        tournament_id = int(request.match_info['id'])

        participants = await db_execute_query(
            "SELECT * FROM tournament_participants WHERE tournament_id = ? ORDER BY registration_date",
            [tournament_id]
        )

        return web.json_response(participants)
    except Exception as e:
        print(f"Error getting tournament participants: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def publish_giveaway_handler(request):
    try:
        giveaway_id = int(request.match_info['id'])
        data = await request.json()
        bot = request.app['bot']

        # Get giveaway details
        giveaways = await db_execute_query("SELECT * FROM giveaways WHERE id = ?", [giveaway_id])
        if not giveaways:
            return web.json_response({"error": "Giveaway not found"}, status=404)

        giveaway = giveaways[0]

        # Create message text
        message_text = f"🎁 <b>{giveaway['title']}</b>\n\n"
        if giveaway['description']:
            message_text += f"{giveaway['description']}\n\n"
        if giveaway['end_date']:
            message_text += f"⏰ Окончание: {giveaway['end_date']}\n\n"
        message_text += "Нажмите кнопку ниже, чтобы участвовать!"

        # Create keyboard
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎮 Участвовать (0)", callback_data=f"giveaway_participate_{giveaway_id}")]
        ])

        # Send message to channel
        message = await bot.send_message(
            chat_id=CHANNEL_ID,
            text=message_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

        return web.json_response({"message": "Giveaway published successfully", "message_id": message.message_id})
    except Exception as e:
        print(f"Error publishing giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_app(bot=None):
    app = web.Application()

    if bot:
        app['bot'] = bot

    # Static files
    app.router.add_static('/static', 'static')

    # Routes
    app.router.add_get('/', index_handler)
    app.router.add_get('/health', health_handler)

    # API routes
    app.router.add_get('/api/giveaways', get_giveaways_handler)
    app.router.add_post('/api/giveaways', create_giveaway_handler)
    app.router.add_post('/api/giveaways/{id}/finish', finish_giveaway_handler)
    app.router.add_delete('/api/giveaways/{id}', delete_giveaway_handler)
    app.router.add_post('/api/giveaways/{id}/publish', publish_giveaway_handler)

    app.router.add_get('/api/tournaments', get_tournaments_handler)
    app.router.add_post('/api/tournaments', create_tournament_handler)
    app.router.add_post('/api/tournaments/{id}/close', close_tournament_handler)
    app.router.add_delete('/api/tournaments/{id}', delete_tournament_handler)
    app.router.add_get('/api/tournaments/{id}/participants', get_tournament_participants_handler)

    return app