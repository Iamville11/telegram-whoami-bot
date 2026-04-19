"""
db.py
SQLite database operations for "Who am I?" game
Handles game state, players, and character assignments
"""

import aiosqlite
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class GameState:
    """Game state data structure"""
    chat_id: int
    game_id: str
    players_queue: List[int]  # user_ids in order
    current_turn_index: int
    user_cards: Dict[int, str]  # user_id -> character_name
    last_question_message_id: Optional[int]
    answered_users: List[int]  # users who reacted to current question
    game_status: str  # 'waiting', 'active', 'finished'
    created_at: str
    updated_at: str

class Database:
    """SQLite database operations"""
    
    def __init__(self, db_path: str = "whoami_bot.db"):
        self.db_path = db_path
        self._lock = asyncio.Lock()
    
    async def init(self):
        """Initialize database tables"""
        async with self._lock:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS games (
                        chat_id INTEGER PRIMARY KEY,
                        game_id TEXT NOT NULL,
                        players_queue TEXT NOT NULL,
                        current_turn_index INTEGER NOT NULL DEFAULT 0,
                        user_cards TEXT NOT NULL,
                        last_question_message_id INTEGER,
                        answered_users TEXT NOT NULL DEFAULT '[]',
                        game_status TEXT NOT NULL DEFAULT 'waiting',
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS players (
                        chat_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        username TEXT,
                        joined_at TEXT NOT NULL,
                        PRIMARY KEY (chat_id, user_id)
                    )
                """)
                
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS game_stats (
                        chat_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        games_played INTEGER DEFAULT 0,
                        games_won INTEGER DEFAULT 0,
                        PRIMARY KEY (chat_id, user_id)
                    )
                """)
                
                await db.commit()
                logger.info("Database initialized successfully")
    
    async def create_game(self, chat_id: int, game_id: str) -> bool:
        """Create new game session"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    # Check if game already exists
                    cursor = await db.execute(
                        "SELECT game_id FROM games WHERE chat_id = ?",
                        (chat_id,)
                    )
                    if await cursor.fetchone():
                        logger.warning(f"Game already exists for chat {chat_id}")
                        return False
                    
                    now = datetime.now().isoformat()
                    await db.execute("""
                        INSERT INTO games 
                        (chat_id, game_id, players_queue, current_turn_index, 
                         user_cards, answered_users, game_status, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chat_id, game_id, json.dumps([]), 0,
                        json.dumps({}), json.dumps([]), 'waiting',
                        now, now
                    ))
                    await db.commit()
                    logger.info(f"Created game {game_id} for chat {chat_id}")
                    return True
            except Exception as e:
                logger.error(f"Error creating game: {e}")
                return False
    
    async def get_game(self, chat_id: int) -> Optional[GameState]:
        """Get current game state"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute(
                        "SELECT * FROM games WHERE chat_id = ?",
                        (chat_id,)
                    )
                    row = await cursor.fetchone()
                    if not row:
                        return None
                    
                    columns = [description[0] for description in cursor.description]
                    game_data = dict(zip(columns, row))
                    
                    return GameState(
                        chat_id=game_data['chat_id'],
                        game_id=game_data['game_id'],
                        players_queue=json.loads(game_data['players_queue']),
                        current_turn_index=game_data['current_turn_index'],
                        user_cards=json.loads(game_data['user_cards']),
                        last_question_message_id=game_data['last_question_message_id'],
                        answered_users=json.loads(game_data['answered_users']),
                        game_status=game_data['game_status'],
                        created_at=game_data['created_at'],
                        updated_at=game_data['updated_at']
                    )
            except Exception as e:
                logger.error(f"Error getting game: {e}")
                return None
    
    async def update_game(self, game: GameState) -> bool:
        """Update game state"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    game.updated_at = datetime.now().isoformat()
                    await db.execute("""
                        UPDATE games SET
                            players_queue = ?,
                            current_turn_index = ?,
                            user_cards = ?,
                            last_question_message_id = ?,
                            answered_users = ?,
                            game_status = ?,
                            updated_at = ?
                        WHERE chat_id = ?
                    """, (
                        json.dumps(game.players_queue),
                        game.current_turn_index,
                        json.dumps(game.user_cards),
                        game.last_question_message_id,
                        json.dumps(game.answered_users),
                        game.game_status,
                        game.updated_at,
                        game.chat_id
                    ))
                    await db.commit()
                    return True
            except Exception as e:
                logger.error(f"Error updating game: {e}")
                return False
    
    async def delete_game(self, chat_id: int) -> bool:
        """Delete game session"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        "DELETE FROM games WHERE chat_id = ?",
                        (chat_id,)
                    )
                    await db.commit()
                    logger.info(f"Deleted game for chat {chat_id}")
                    return True
            except Exception as e:
                logger.error(f"Error deleting game: {e}")
                return False
    
    async def add_player(self, chat_id: int, user_id: int, username: str) -> bool:
        """Add player to game"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    now = datetime.now().isoformat()
                    await db.execute("""
                        INSERT OR REPLACE INTO players (chat_id, user_id, username, joined_at)
                        VALUES (?, ?, ?, ?)
                    """, (chat_id, user_id, username, now))
                    
                    # Initialize stats if not exists
                    await db.execute("""
                        INSERT OR IGNORE INTO game_stats (chat_id, user_id)
                        VALUES (?, ?)
                    """, (chat_id, user_id))
                    
                    await db.commit()
                    logger.info(f"Added player {user_id} to chat {chat_id}")
                    return True
            except Exception as e:
                logger.error(f"Error adding player: {e}")
                return False
    
    async def remove_player(self, chat_id: int, user_id: int) -> bool:
        """Remove player from game"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        "DELETE FROM players WHERE chat_id = ? AND user_id = ?",
                        (chat_id, user_id)
                    )
                    await db.commit()
                    logger.info(f"Removed player {user_id} from chat {chat_id}")
                    return True
            except Exception as e:
                logger.error(f"Error removing player: {e}")
                return False
    
    async def get_players(self, chat_id: int) -> List[Tuple[int, str]]:
        """Get all players in chat"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute(
                        "SELECT user_id, username FROM players WHERE chat_id = ?",
                        (chat_id,)
                    )
                    return await cursor.fetchall()
            except Exception as e:
                logger.error(f"Error getting players: {e}")
                return []
    
    async def update_game_stats(self, chat_id: int, user_id: int, won: bool = False) -> bool:
        """Update player statistics"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    if won:
                        await db.execute("""
                            UPDATE game_stats 
                            SET games_played = games_played + 1,
                                games_won = games_won + 1
                            WHERE chat_id = ? AND user_id = ?
                        """, (chat_id, user_id))
                    else:
                        await db.execute("""
                            UPDATE game_stats 
                            SET games_played = games_played + 1
                            WHERE chat_id = ? AND user_id = ?
                        """, (chat_id, user_id))
                    await db.commit()
                    return True
            except Exception as e:
                logger.error(f"Error updating stats: {e}")
                return False
    
    async def get_player_stats(self, chat_id: int, user_id: int) -> Optional[Dict]:
        """Get player statistics"""
        async with self._lock:
            try:
                async with aiosqlite.connect(self.db_path) as db:
                    cursor = await db.execute(
                        "SELECT games_played, games_won FROM game_stats WHERE chat_id = ? AND user_id = ?",
                        (chat_id, user_id)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {"games_played": row[0], "games_won": row[1]}
                    return None
            except Exception as e:
                logger.error(f"Error getting player stats: {e}")
                return None

# Global database instance
db = Database()
