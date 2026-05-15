#!/usr/bin/env python3
"""Discord Release Bot - Main Entry Point"""

import asyncio
import os
from dotenv import load_dotenv

from src.bot import setup_bot
from src.logger import logger

def main():
    """Main entry point"""
    # Load environment variables
    load_dotenv()
    logger.info("Environment variables loaded")

    # Get token
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set")
        return

    logger.info("Starting Discord bot...")

    # Setup and run bot
    bot = asyncio.run(setup_bot())

    # Run bot
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Bot shutting down...")
    except Exception as e:
        logger.error(f"Bot error: {e}")
        raise

if __name__ == "__main__":
    main()
