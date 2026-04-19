# Telegram Bot - "Who Am I?" Game

Telegram bot for the classic "Who Am I?" guessing game for 3 players.

## Game Rules

**Goal**: Guess the character written on your forehead by asking yes/no questions.

**How it works**:
1. Each player gets a secret character (famous person from movies, books, etc.)
2. Players take turns asking yes/no questions about their character
3. If you get a "yes" answer, you can continue asking questions
4. If you get a "no" answer, your turn ends
5. First player to guess their character wins!

## Local Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Get a Telegram bot token:
   - Talk to @BotFather on Telegram
   - Create a new bot
   - Copy the bot token

3. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Add your bot token to `.env` file

4. Run the bot:
```bash
python bot.py
```

## Deployment Options

### Option 1: Render (Recommended)
1. Push your code to GitHub
2. Sign up at [render.com](https://render.com)
3. Create a new "Web Service"
4. Connect your GitHub repository
5. Set environment variable `BOT_TOKEN` to your bot token
6. Deploy!

### Option 2: Railway
1. Sign up at [railway.app](https://railway.app)
2. Create new project from GitHub
3. Add `BOT_TOKEN` environment variable
4. Deploy automatically

### Option 3: PythonAnywhere
1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. Upload your files
3. Install requirements in virtual environment
4. Set up a scheduled task to run the bot
5. Add `BOT_TOKEN` environment variable

### Option 4: Fly.io
1. Install Fly CLI
2. Run: `fly launch`
3. Set environment variable: `fly secrets set BOT_TOKEN=your_token`
4. Deploy: `fly deploy`

## How to Play

1. Start a game with `/start` in any group chat
2. 3 players need to join by clicking the "Join Game" button
3. Once all players join, the bot will send each player their character via private message
4. Players take turns asking questions (max 5 questions per turn)
5. To make a guess, just type the character name (without a question mark)
6. First player to guess correctly wins!

## Features

- Supports exactly 3 players
- 24 pre-defined characters from popular media
- Private character assignment
- Turn-based questioning system
- Yes/No answer validation
- Automatic game state management

## Characters Included

The bot includes characters from:
- Harry Potter
- Sherlock Holmes
- James Bond
- Marvel Superheroes
- Star Wars
- Lord of the Rings
- DC Comics
- Nintendo/Sonic
- Disney's Frozen

## Commands

- `/start` - Start a new game
- `/cancel` - Cancel current game

## Notes

- Players must start a private chat with the bot to receive their character
- Questions must end with "?" to be treated as questions
- Non-questions are treated as character guesses
- The bot supports "yes/no" answers in multiple languages
