import logging
import random
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from telegram.ext import ConversationHandler

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Game states
WAITING_FOR_PLAYERS, CHARACTER_ASSIGNMENT, QUESTIONING, GAME_OVER = range(4)

# Game data
games = {}

class Game:
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.players = []
        self.characters = {}
        self.current_player_index = 0
        self.game_state = WAITING_FOR_PLAYERS
        self.questions_remaining = 0
        self.max_questions_per_turn = 5
        
    def add_player(self, user_id, username):
        if len(self.players) < 3 and user_id not in [p['id'] for p in self.players]:
            self.players.append({'id': user_id, 'username': username})
            return True
        return False
    
    def is_ready(self):
        return len(self.players) == 3
    
    def assign_characters(self):
        characters = [
            "Harry Potter", "Hermione Granger", "Ron Weasley",
            "Sherlock Holmes", "Doctor Watson", "James Bond",
            "Spider-Man", "Iron Man", "Captain America",
            "Darth Vader", "Yoda", "Luke Skywalker",
            "Frodo Baggins", "Gandalf", "Aragorn",
            "Batman", "Superman", "Wonder Woman",
            "Pikachu", "Mario", "Sonic",
            "Elsa", "Anna", "Olaf"
        ]
        
        selected_chars = random.sample(characters, 3)
        
        for i, player in enumerate(self.players):
            self.characters[player['id']] = selected_chars[i]
    
    def get_current_player(self):
        if self.current_player_index < len(self.players):
            return self.players[self.current_player_index]
        return None
    
    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.questions_remaining = self.max_questions_per_turn
    
    def get_character(self, user_id):
        return self.characters.get(user_id, "Unknown")
    
    def check_guess(self, user_id, guess):
        correct_character = self.characters.get(user_id, "")
        return guess.lower() == correct_character.lower()

def start(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id in games:
        update.message.reply_text("Game already in progress in this chat!")
        return ConversationHandler.END
    
    # Create new game
    game = Game(chat_id)
    games[chat_id] = game
    
    # Add first player
    game.add_player(user.id, user.username or user.first_name)
    
    keyboard = [[InlineKeyboardButton("Join Game", callback_data=f"join_{user.id}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(
        f"Welcome to 'Who Am I?' game! {user.username or user.first_name} started the game.\n"
        f"Need 2 more players to join.\n"
        f"Players joined: {len(game.players)}/3",
        reply_markup=reply_markup
    )
    
    return WAITING_FOR_PLAYERS

def join_game(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    query.answer()
    
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id not in games:
        query.edit_message_text("No game in progress. Start a new game with /start")
        return ConversationHandler.END
    
    game = games[chat_id]
    
    if game.add_player(user.id, user.username or user.first_name):
        players_text = "\n".join([f"Player {i+1}: {p['username']}" for i, p in enumerate(game.players)])
        
        if game.is_ready():
            # Start character assignment
            game.assign_characters()
            game.game_state = CHARACTER_ASSIGNMENT
            
            # Send private messages with characters
            for player in game.players:
                character = game.get_character(player['id'])
                try:
                    context.bot.send_message(
                        chat_id=player['id'],
                        text=f"Your character is: {character}\nDon't tell anyone! Keep it secret!"
                    )
                except:
                    query.edit_message_text("I can't send you a private message. Please start a chat with me first!")
                    return ConversationHandler.END
            
            query.edit_message_text(
                f"All players joined! Game starting...\n"
                f"Characters assigned via private messages.\n"
                f"Players:\n{players_text}\n"
                f"{game.players[0]['username']} goes first!"
            )
            
            game.current_player_index = 0
            game.questions_remaining = game.max_questions_per_turn
            
            # Ask first player to start
            current_player = game.get_current_player()
            context.bot.send_message(
                chat_id=chat_id,
                text=f"{current_player['username']}, ask your first question! (You have {game.questions_remaining} questions remaining)"
            )
            
            return QUESTIONING
        else:
            keyboard = [[InlineKeyboardButton("Join Game", callback_data=f"join_{user.id}")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            query.edit_message_text(
                f"{user.username or user.first_name} joined the game!\n"
                f"Players joined: {len(game.players)}/3\n"
                f"{players_text}",
                reply_markup=reply_markup
            )
    else:
        query.edit_message_text("You're already in the game or the game is full!")
    
    return WAITING_FOR_PLAYERS

def handle_question(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message_text = update.message.text
    
    if chat_id not in games:
        return ConversationHandler.END
    
    game = games[chat_id]
    current_player = game.get_current_player()
    
    if user_id != current_player['id']:
        update.message.reply_text("It's not your turn!")
        return QUESTIONING
    
    # Check if it's a guess (not a question)
    if not message_text.strip().endswith('?'):
        # This is a guess
        if game.check_guess(user_id, message_text):
            update.message.reply_text(f"Congratulations! You guessed it! You are {game.get_character(user_id)}!")
            game.game_state = GAME_OVER
            
            # Show all characters
            results = "Game Over! Here were all the characters:\n"
            for player in game.players:
                results += f"{player['username']}: {game.get_character(player['id'])}\n"
            
            update.message.reply_text(results)
            update.message.reply_text("Start a new game with /start")
            
            return ConversationHandler.END
        else:
            update.message.reply_text("Wrong guess! Try asking more questions.")
            game.next_player()
            next_player = game.get_current_player()
            update.message.reply_text(f"Now it's {next_player['username']}'s turn!")
            return QUESTIONING
    
    # This is a question
    game.questions_remaining -= 1
    
    # Send question to other players for yes/no answers
    other_players = [p for p in game.players if p['id'] != user_id]
    player_mentions = " ".join([f"@{p['username']}" for p in other_players])
    
    update.message.reply_text(
        f"{current_player['username']} asks: {message_text}\n"
        f"{player_mentions} - Please answer with 'Yes' or 'No'"
    )
    
    if game.questions_remaining == 0:
        game.next_player()
        next_player = game.get_current_player()
        update.message.reply_text(f"Questions used! Now it's {next_player['username']}'s turn!")
    
    return QUESTIONING

def handle_answer(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    message_text = update.message.text.lower()
    
    if chat_id not in games:
        return ConversationHandler.END
    
    game = games[chat_id]
    
    if message_text in ['yes', 'no', 'da', 'net', 'yes.', 'no.', 'y', 'n']:
        # Valid answer
        return QUESTIONING
    else:
        update.message.reply_text("Please answer with 'Yes' or 'No' only!")
        return QUESTIONING

def cancel(update: Update, context: CallbackContext) -> int:
    chat_id = update.effective_chat.id
    
    if chat_id in games:
        del games[chat_id]
    
    update.message.reply_text("Game cancelled. Start a new game with /start")
    return ConversationHandler.END

def main():
    # Get bot token from environment variables
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("No BOT_TOKEN found in environment variables!")
        return
    
    # Create the Updater and pass it your bot's token
    updater = Updater(bot_token, use_context=True)
    
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    
    # Add conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_PLAYERS: [CallbackQueryHandler(join_game, pattern='^join_')],
            QUESTIONING: [MessageHandler(Filters.text & ~Filters.command, handle_question)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    dp.add_handler(conv_handler)
    
    # Start the Bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
