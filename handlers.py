"""
handlers.py
Command handlers for "Who am I?" Telegram bot
"""

import logging
from typing import Optional

from aiogram import Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ChatMemberUpdated, ChatMemberAdministrator, ChatMemberMember

from db import db
from game import GameManager
from characters import get_all_categories

logger = logging.getLogger(__name__)

# Create router
router = Router()

def is_group_chat(message: Message) -> bool:
    """Check if message is from group chat"""
    return message.chat.type in ['group', 'supergroup']

def get_user_mention(user: types.User) -> str:
    """Get user mention with name"""
    name = user.full_name or user.username or f"User {user.id}"
    return f"@{user.username}" if user.username else name

async def is_user_admin(message: Message) -> bool:
    """Check if user is admin in group"""
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in ['administrator', 'creator']
    except:
        return False

@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command"""
    if not is_group_chat(message.chat):
        await message.answer(
            "This bot only works in group chats!\n"
            "Add me to a group and use /help to see available commands."
        )
        return
    
    await message.answer(
        "Welcome to 'Who am I?' game! \ud83c\udfad\n\n"
        "Available commands:\n"
        "/join - Join the game\n"
        "/start_game - Start game (3+ players needed)\n"
        "/guess <name> - Guess your character\n"
        "/skip - Skip your turn\n"
        "/stop - Stop current game\n"
        "/status - Show game status\n"
        "/help - Show this help"
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
    \ud83c\udfaf **Who am I? Game Rules**
    
    **How to play:**
    1. Join game with /join
    2. Start game with /start_game (3+ players needed)
    3. Each player gets a secret character
    4. Ask yes/no questions to guess your character
    5. Others react with \ud83d\udc4d (yes) or \ud83d\udc4e (no)
    6. First to guess correctly wins!
    
    **Commands:**
    /join - Join the game
    /start_game - Start game (3+ players needed)
    /guess <name> - Guess your character
    /skip - Skip your turn
    /stop - Stop current game
    /status - Show game status
    /players - Show all players
    /categories - Show character categories
    
    **Gameplay:**
    - Ask questions in chat during your turn
    - Wait for reactions from other players
    - Any \ud83d\udc4e reaction ends your turn
    - All \ud83d\udc4d reactions let you continue
    - 5 minutes limit per turn
    """
    
    await message.answer(help_text, parse_mode="Markdown")

@router.message(Command("join"))
async def cmd_join(message: Message):
    """Handle /join command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    chat_id = message.chat.id
    
    # Add player to database
    success = await db.add_player(chat_id, user_id, username or "")
    
    if success:
        players = await db.get_players(chat_id)
        player_names = [p[1] or f"Player {p[0]}" for p in players]
        
        await message.answer(
            f"{get_user_mention(message.from_user)} joined the game! \n\n"
            f"Players ({len(players)}): {', '.join(player_names)}\n\n"
            f"Need {3 - len(players)} more players to start!"
        )
    else:
        await message.answer("Failed to join game. Try again!")

@router.message(Command("start_game"))
async def cmd_start_game(message: Message, game_manager: GameManager):
    """Handle /start_game command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    chat_id = message.chat.id
    
    # Start game
    success, result = await game_manager.start_game(chat_id)
    
    if success:
        # Get game status
        status = await game_manager.get_game_status(chat_id)
        if status:
            await message.answer(
                f"\ud83c\udfae **Game Started!**\n\n"
                f"Players: {', '.join(status['players'])}\n"
                f"Current turn: {status['current_player']}\n\n"
                f"{status['current_player']}, ask your first question!",
                parse_mode="Markdown"
            )
    else:
        await message.answer(f"Failed to start game: {result}")

@router.message(Command("guess"))
async def cmd_guess(message: Message, game_manager: GameManager):
    """Handle /guess command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    # Extract guess from command
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Usage: /guess <character name>")
        return
    
    guess = parts[1].strip()
    chat_id = message.chat.id
    
    # Process guess
    success, result = await game_manager.process_guess(message, guess)
    
    if success:
        await message.answer(f"\ud83c\udf89 {result}")
    else:
        await message.answer(f"\u274c {result}")

@router.message(Command("skip"))
async def cmd_skip(message: Message, game_manager: GameManager):
    """Handle /skip command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    success, result = await game_manager.skip_turn(chat_id, user_id)
    
    if success:
        # Get next player
        status = await game_manager.get_game_status(chat_id)
        if status and status['current_player']:
            await message.answer(
                f"{result}\n\n"
                f"Next turn: {status['current_player']}"
            )
        else:
            await message.answer(result)
    else:
        await message.answer(result)

@router.message(Command("stop"))
async def cmd_stop(message: Message, game_manager: GameManager):
    """Handle /stop command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    # Check if user is admin or game creator
    is_admin = await is_user_admin(message)
    if not is_admin:
        await message.answer("Only admins can stop the game!")
        return
    
    chat_id = message.chat.id
    
    success = await game_manager.stop_game(chat_id)
    
    if success:
        await message.answer("Game stopped! Use /start_game to play again.")
    else:
        await message.answer("No active game to stop.")

@router.message(Command("status"))
async def cmd_status(message: Message, game_manager: GameManager):
    """Handle /status command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    chat_id = message.chat.id
    
    # Get game status
    status = await game_manager.get_game_status(chat_id)
    
    if not status:
        await message.answer("No active game. Use /start_game to begin!")
        return
    
    status_text = f"""
    \ud83d\udcca **Game Status**
    
    Status: {status['status']}
    Players: {status['total_players']}
    Current turn: {status['current_player'] or 'None'}
    
    Players: {', '.join(status['players'])}
    """
    
    await message.answer(status_text, parse_mode="Markdown")

@router.message(Command("players"))
async def cmd_players(message: Message):
    """Handle /players command"""
    if not is_group_chat(message.chat):
        await message.answer("This command only works in group chats!")
        return
    
    chat_id = message.chat.id
    
    players = await db.get_players(chat_id)
    if not players:
        await message.answer("No players yet. Use /join to join!")
        return
    
    player_list = []
    for user_id, username in players:
        name = username or f"Player {user_id}"
        player_list.append(f" @{username}" if username else f" {name}")
    
    await message.answer(
        f"\ud83d\udc65 **Players ({len(players)}):**\n"
        f"{''.join(player_list)}"
    )

@router.message(Command("categories"))
async def cmd_categories(message: Message):
    """Handle /categories command"""
    categories = get_all_categories()
    await message.answer(
        f"\ud83d\udcda **Character Categories:**\n"
        f"{', '.join(sorted(categories))}"
    )

# Handle regular messages (questions)
@router.message(F.text & ~F.command)
async def handle_question(message: Message, game_manager: GameManager):
    """Handle regular messages as questions"""
    if not is_group_chat(message.chat):
        return
    
    chat_id = message.chat.id
    
    # Process as question
    success, result = await game_manager.process_question(message)
    
    if success:
        # Send reaction request
        await message.reply(
            f"\u2753 **Question asked!**\n\n"
            f"Other players, react with:\n"
            f"\ud83d\udc4d = Yes\n"
            f"\ud83d\udc4e = No\n\n"
            f"Waiting for reactions...",
            parse_mode="Markdown"
        )
    elif result and "not your turn" in result.lower():
        await message.reply(f"\u23f0 {result}")

# Handle message reactions
@router.message_reaction()
async def handle_reaction(reaction: types.MessageReactionUpdated, game_manager: GameManager):
    """Handle message reactions"""
    if reaction.chat.type not in ['group', 'supergroup']:
        return
    
    # Process reaction
    result = await game_manager.process_reaction(reaction)
    
    if result:
        try:
            await reaction.bot.send_message(reaction.chat.id, result)
        except Exception as e:
            logger.error(f"Error sending reaction result: {e}")

# Handle chat member updates (player left)
@router.chat_member()
async def handle_chat_member_update(event: ChatMemberUpdated, game_manager: GameManager):
    """Handle when user leaves chat"""
    if event.chat.type not in ['group', 'supergroup']:
        return
    
    user_id = event.new_chat_member.user.id
    chat_id = event.chat.id
    
    # Check if user was a player
    if event.old_chat_member.status in ['member', 'administrator', 'creator'] and \
       event.new_chat_member.status == 'left':
        
        # Remove from players
        await db.remove_player(chat_id, user_id)
        
        # Check if it was current player's turn
        current_player = await game_manager.get_current_player(chat_id)
        if current_player == user_id:
            # Skip turn
            await game_manager.skip_turn(chat_id, user_id)
            try:
                await event.bot.send_message(
                    chat_id,
                    f"Player {user_id} left the game. Turn skipped!"
                )
            except Exception as e:
                logger.error(f"Error sending leave message: {e}")

# Handle errors
@router.errors()
async def error_handler(event: types.ErrorEvent):
    """Handle errors"""
    logger.error(f"Error in handler: {event.exception}")
    
    try:
        if event.update.message:
            await event.update.message.answer(
                "An error occurred. Please try again later."
            )
    except Exception:
        pass
