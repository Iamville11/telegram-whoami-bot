"""
game.py
Core game logic for "Who am I?" game
Handles turn management, reactions, and game flow
"""

import asyncio
import random
import uuid
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
import logging

from aiogram import Bot, types
from aiogram.types import MessageReactionUpdated, ReactionTypeEmoji

from db import Database, GameState
from characters import Character, get_random_characters, get_character_by_name

logger = logging.getLogger(__name__)

class GameManager:
    """Manages game state and logic"""
    
    def __init__(self, bot: Bot, database: Database):
        self.bot = bot
        self.db = database
        self._locks: Dict[int, asyncio.Lock] = {}  # chat_id -> lock
        self._timers: Dict[int, asyncio.Task] = {}  # chat_id -> timer task
    
    def get_lock(self, chat_id: int) -> asyncio.Lock:
        """Get or create lock for chat"""
        if chat_id not in self._locks:
            self._locks[chat_id] = asyncio.Lock()
        return self._locks[chat_id]
    
    async def start_game(self, chat_id: int) -> tuple[bool, str]:
        """Start new game session"""
        lock = self.get_lock(chat_id)
        async with lock:
            # Check if game already exists
            existing_game = await self.db.get_game(chat_id)
            if existing_game and existing_game.game_status == 'active':
                return False, "Game already in progress!"
            
            # Get players
            players = await self.db.get_players(chat_id)
            if len(players) < 3:
                return False, "Need at least 3 players to start!"
            
            # Create new game
            game_id = str(uuid.uuid4())[:8]
            success = await self.db.create_game(chat_id, game_id)
            if not success:
                return False, "Failed to create game!"
            
            # Get game state
            game = await self.db.get_game(chat_id)
            
            # Setup players queue
            player_ids = [p[0] for p in players]
            random.shuffle(player_ids)
            game.players_queue = player_ids
            
            # Assign characters
            characters = get_random_characters(len(player_ids))
            for i, user_id in enumerate(player_ids):
                game.user_cards[user_id] = characters[i].name
            
            game.game_status = 'active'
            game.current_turn_index = 0
            game.answered_users = []
            
            # Save game state
            await self.db.update_game(game)
            
            # Cancel any existing timer
            if chat_id in self._timers:
                self._timers[chat_id].cancel()
            
            # Start turn timer
            await self._start_turn_timer(chat_id)
            
            return True, f"Game started! {len(players)} players joined."
    
    async def get_current_player(self, chat_id: int) -> Optional[int]:
        """Get current player user_id"""
        game = await self.db.get_game(chat_id)
        if not game or game.game_status != 'active':
            return None
        
        if game.current_turn_index >= len(game.players_queue):
            return None
        
        return game.players_queue[game.current_turn_index]
    
    async def process_question(self, message: types.Message) -> tuple[bool, str]:
        """Process player's question"""
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        lock = self.get_lock(chat_id)
        async with lock:
            game = await self.db.get_game(chat_id)
            if not game or game.game_status != 'active':
                return False, "No active game!"
            
            # Check if it's player's turn
            current_player = game.players_queue[game.current_turn_index]
            if user_id != current_player:
                return False, "It's not your turn!"
            
            # Validate question (basic check)
            question_text = message.text.strip()
            if len(question_text) < 3:
                return False, "Question too short!"
            if len(question_text) > 200:
                return False, "Question too long!"
            
            # Reset answered users for new question
            game.answered_users = []
            game.last_question_message_id = message.message_id
            
            # Save game state
            await self.db.update_game(game)
            
            # Reset turn timer
            await self._reset_turn_timer(chat_id)
            
            return True, "Question sent! Waiting for reactions..."
    
    async def process_reaction(self, reaction: MessageReactionUpdated) -> Optional[str]:
        """Process reaction to question"""
        chat_id = reaction.chat.id
        user_id = reaction.user.id
        
        lock = self.get_lock(chat_id)
        async with lock:
            game = await self.db.get_game(chat_id)
            if not game or game.game_status != 'active':
                return None
            
            # Check if reaction is to last question
            if game.last_question_message_id != reaction.message_id:
                return None
            
            # Check if user is in game
            if user_id not in game.players_queue:
                return None
            
            # Check if user already answered
            if user_id in game.answered_users:
                return None
            
            # Process reaction
            new_reaction = None
            if reaction.new_reaction:
                if isinstance(reaction.new_reaction, ReactionTypeEmoji):
                    new_reaction = reaction.new_reaction.emoji
            
            # Only process thumbs up/down
            if new_reaction not in ['\U0001F44D', '\U0001F44E']:  # thumbs up/down
                return None
            
            # Add to answered users
            game.answered_users.append(user_id)
            
            # Check for thumbs down (any thumbs down ends turn)
            if new_reaction == '\U0001F44E':  # thumbs down
                await self._next_turn(chat_id)
                return "Someone answered NO! Turn passed."
            
            # Check if all players answered (except current player)
            other_players = [p for p in game.players_queue if p != game.players_queue[game.current_turn_index]]
            answered_others = [u for u in game.answered_users if u != game.players_queue[game.current_turn_index]]
            
            if len(answered_others) >= len(other_players):
                # All other players answered with thumbs up
                return "All players answered YES! Ask another question."
            
            # Save state
            await self.db.update_game(game)
            return None
    
    async def process_guess(self, message: types.Message, guess: str) -> tuple[bool, str]:
        """Process character guess"""
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        lock = self.get_lock(chat_id)
        async with lock:
            game = await self.db.get_game(chat_id)
            if not game or game.game_status != 'active':
                return False, "No active game!"
            
            # Check if it's player's turn
            current_player = game.players_queue[game.current_turn_index]
            if user_id != current_player:
                return False, "It's not your turn!"
            
            # Get player's character
            player_character = game.user_cards.get(user_id)
            if not player_character:
                return False, "Character not found!"
            
            # Check guess
            guessed_character = get_character_by_name(guess)
            if not guessed_character:
                return False, "Character not in database!"
            
            if guessed_character.name.lower() == player_character.lower():
                # Correct guess - player wins!
                await self._end_game(chat_id, user_id)
                await self.db.update_game_stats(chat_id, user_id, won=True)
                return True, f"Correct! You were {player_character}! You won! \ud83c\udf89"
            else:
                # Wrong guess - pass turn
                await self._next_turn(chat_id)
                await self.db.update_game_stats(chat_id, user_id, won=False)
                return False, f"Wrong! You're not {guess}. Turn passed."
    
    async def skip_turn(self, chat_id: int, user_id: int) -> tuple[bool, str]:
        """Skip current turn"""
        lock = self.get_lock(chat_id)
        async with lock:
            game = await self.db.get_game(chat_id)
            if not game or game.game_status != 'active':
                return False, "No active game!"
            
            # Check if it's player's turn
            current_player = game.players_queue[game.current_turn_index]
            if user_id != current_player:
                return False, "It's not your turn!"
            
            await self._next_turn(chat_id)
            return True, "Turn skipped!"
    
    async def stop_game(self, chat_id: int) -> bool:
        """Stop current game"""
        lock = self.get_lock(chat_id)
        async with lock:
            game = await self.db.get_game(chat_id)
            if not game:
                return False
            
            # Cancel timer
            if chat_id in self._timers:
                self._timers[chat_id].cancel()
                del self._timers[chat_id]
            
            # Delete game
            await self.db.delete_game(chat_id)
            return True
    
    async def _next_turn(self, chat_id: int):
        """Move to next player's turn"""
        game = await self.db.get_game(chat_id)
        if not game:
            return
        
        # Move to next player
        game.current_turn_index = (game.current_turn_index + 1) % len(game.players_queue)
        game.answered_users = []
        game.last_question_message_id = None
        
        await self.db.update_game(game)
        
        # Reset turn timer
        await self._reset_turn_timer(chat_id)
    
    async def _end_game(self, chat_id: int, winner_id: int):
        """End game with winner"""
        game = await self.db.get_game(chat_id)
        if not game:
            return
        
        game.game_status = 'finished'
        await self.db.update_game(game)
        
        # Cancel timer
        if chat_id in self._timers:
            self._timers[chat_id].cancel()
            del self._timers[chat_id]
    
    async def _start_turn_timer(self, chat_id: int):
        """Start 5-minute turn timer"""
        if chat_id in self._timers:
            self._timers[chat_id].cancel()
        
        self._timers[chat_id] = asyncio.create_task(
            self._turn_timeout(chat_id)
        )
    
    async def _reset_turn_timer(self, chat_id: int):
        """Reset turn timer"""
        await self._start_turn_timer(chat_id)
    
    async def _turn_timeout(self, chat_id: int):
        """Handle turn timeout"""
        await asyncio.sleep(300)  # 5 minutes (300 seconds)
        
        try:
            lock = self.get_lock(chat_id)
            async with lock:
                game = await self.db.get_game(chat_id)
                if not game or game.game_status != 'active':
                    return
                
                current_player = game.players_queue[game.current_turn_index]
                
                # Send timeout message
                try:
                    await self.bot.send_message(
                        chat_id,
                        f"Time's up for player {current_player}! Turn skipped."
                    )
                except Exception as e:
                    logger.error(f"Error sending timeout message: {e}")
                
                # Move to next turn
                await self._next_turn(chat_id)
                
        except asyncio.CancelledError:
            # Timer was cancelled
            pass
        except Exception as e:
            logger.error(f"Error in turn timeout: {e}")
    
    async def get_game_status(self, chat_id: int) -> Optional[Dict]:
        """Get current game status for display"""
        game = await self.db.get_game(chat_id)
        if not game:
            return None
        
        players = await self.db.get_players(chat_id)
        player_names = {p[0]: p[1] or f"Player {p[0]}" for p in players}
        
        current_player = None
        if game.game_status == 'active' and game.current_turn_index < len(game.players_queue):
            current_player_id = game.players_queue[game.current_turn_index]
            current_player = player_names.get(current_player_id, "Unknown")
        
        return {
            "status": game.game_status,
            "players": [player_names.get(pid, "Unknown") for pid in game.players_queue],
            "current_player": current_player,
            "answered_count": len(game.answered_users),
            "total_players": len(game.players_queue)
        }
    
    async def cleanup(self):
        """Cleanup timers and locks"""
        for timer in self._timers.values():
            timer.cancel()
        self._timers.clear()
        self._locks.clear()
