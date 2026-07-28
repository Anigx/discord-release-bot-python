import os
from typing import Optional
from src.logger import logger

def load_config() -> "Config":
    """Load configuration from environment variables"""
    logger.info("Loading configuration from environment variables")
    config = Config()
    return config

class Config:
    """Typed config access from environment variables"""

    def __init__(self):
        self._validate_required_vars()

    def _validate_required_vars(self):
        """Validate that all required environment variables are set"""
        required_vars = [
            'DISCORD_TOKEN',
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        logger.info("All required environment variables are set")

    @property
    def bot_token(self) -> str:
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            raise ValueError("DISCORD_TOKEN environment variable not set")
        return token

    @property
    def github_token(self) -> Optional[str]:
        token = os.getenv('GITHUB_TOKEN', '').strip()
        return token if token else None
