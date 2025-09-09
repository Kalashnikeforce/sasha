
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
        
        # Add participant count for each giveaway
        for giveaway in giveaways:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM giveaway_participants WHERE giveaway_id = $1",
                [giveaway['id']]
            )
            giveaway['participants_count'] = participants[0]['count'] if participants else 0
        
        return web.json_response(giveaways)
    except Exception as e:
        print(f"Error getting giveaways: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def get_tournaments_handler(request):
    try:
        tournaments = await db_execute_query("SELECT * FROM tournaments ORDER BY created_date DESC")
        
        # Add participant count for each tournament
        for tournament in tournaments:
            participants = await db_execute_query(
                "SELECT COUNT(*) as count FROM tournament_participants WHERE tournament_id = $1",
                [tournament['id']]
            )
            tournament['participants_count'] = participants[0]['count'] if participants else 0
        
        return web.json_response(tournaments)
    except Exception as e:
        print(f"Error getting tournaments: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_giveaway_handler(request):
    try:
        data = await request.json()
        
        giveaway_id = await db_execute_update('''
            INSERT INTO giveaways (title, description, end_date, winners_count)
            VALUES ($1, $2, $3, $4) RETURNING id
        ''', [
            data['title'],
            data.get('description', ''),
            data.get('end_date'),
            data.get('winners_count', 1)
        ])
        
        return web.json_response({"success": True, "giveaway_id": giveaway_id})
    except Exception as e:
        print(f"Error creating giveaway: {e}")
        return web.json_response({"error": str(e)}, status=500)

async def create_tournament_handler(request):
    try:
        data = await request.json()
        
        tournament_id = await db_execute_update('''
            INSERT INTO tournaments (title, description, start_date, winners_count)
            VALUES ($1, $2, $3, $4) RETURNING id
        ''', [
            data['title'],
            data.get('description', ''),
            data.get('start_date'),
            data.get('winners_count', 1)
        ])
        
        return web.json_response({"success": True, "tournament_id": tournament_id})
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

async def create_app(bot):
    app = web.Application()
    
    # Routes
    app.router.add_get('/', index_handler)
    app.router.add_get('/health', health_handler)
    
    # API routes
    app.router.add_get('/api/giveaways', get_giveaways_handler)
    app.router.add_get('/api/tournaments', get_tournaments_handler)
    app.router.add_post('/api/giveaways', create_giveaway_handler)
    app.router.add_post('/api/tournaments', create_tournament_handler)
    app.router.add_delete('/api/giveaways/{giveaway_id}', delete_giveaway_handler)
    app.router.add_delete('/api/tournaments/{tournament_id}', delete_tournament_handler)
    app.router.add_get('/api/giveaways/{giveaway_id}/participants', get_giveaway_participants_handler)
    app.router.add_get('/api/tournaments/{tournament_id}/participants', get_tournament_participants_handler)
    app.router.add_post('/api/giveaways/{giveaway_id}/draw', draw_giveaway_winners_handler)
    
    # Static files
    app.router.add_static('/', 'static', name='static')
    
    return app
