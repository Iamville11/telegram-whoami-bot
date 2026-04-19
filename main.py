"""
main.py
Entry point for "Who am I?" Telegram bot
Configuration and bot startup
"""

import asyncio
import logging
import signal
import sys
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from db import db
from game import GameManager
from handlers import router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class WhoAmIBot:
    """Main bot class"""
    
    def __init__(self):
        self.bot = None
        self.dp = None
        self.game_manager = None
        self._running = False
    
    async def init(self):
        """Initialize bot components"""
        # Get bot token
        token = os.getenv('BOT_TOKEN')
        if not token:
            logger.error("BOT_TOKEN not found in environment variables!")
            sys.exit(1)
        
        # Initialize bot
        self.bot = Bot(
            token=token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True
            )
        )
        
        # Initialize dispatcher
        self.dp = Dispatcher()
        
        # Initialize database
        await db.init()
        
        # Initialize game manager
        self.game_manager = GameManager(self.bot, db)
        
        # Include router
        self.dp.include_router(router)
        
        # Setup signal handlers
        self._setup_signal_handlers()
        
        logger.info("Bot initialized successfully")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self._running = False
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def run(self):
        """Run the bot"""
        await self.init()
        
        self._running = True
        logger.info("Starting bot polling...")
        
        # Start polling
        try:
            await self.dp.start_polling(
                self.bot,
                handle_signals=False  # We handle signals ourselves
            )
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        except Exception as e:
            logger.error(f"Bot error: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down bot...")
        
        try:
            # Stop polling
            if self.dp:
                await self.dp.stop_polling()
            
            # Cleanup game manager
            if self.game_manager:
                await self.game_manager.cleanup()
            
            # Close bot session
            if self.bot:
                await self.bot.session.close()
            
            logger.info("Bot shutdown complete")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Main entry point"""
    bot = WhoAmIBot()
    await bot.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
