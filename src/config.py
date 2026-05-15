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
            'DISCORD_CLIENT_ID',
            'DISCORD_ANNOUNCEMENT_CHANNEL_ID',
            'GITHUB_OWNER',
            'GITHUB_REPO'
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
    def bot_client_id(self) -> str:
        client_id = os.getenv('DISCORD_CLIENT_ID')
        if not client_id:
            raise ValueError("DISCORD_CLIENT_ID environment variable not set")
        return client_id

    @property
    def bot_guild_id(self) -> Optional[str]:
        guild_id = os.getenv('DISCORD_GUILD_ID', '').strip()
        return guild_id if guild_id else None

    @property
    def bot_announcement_channel_id(self) -> str:
        channel_id = os.getenv('DISCORD_ANNOUNCEMENT_CHANNEL_ID')
        if not channel_id:
            raise ValueError("DISCORD_ANNOUNCEMENT_CHANNEL_ID environment variable not set")
        return channel_id

    @property
    def github_owner(self) -> str:
        owner = os.getenv('GITHUB_OWNER')
        if not owner:
            raise ValueError("GITHUB_OWNER environment variable not set")
        return owner

    @property
    def github_repo(self) -> str:
        repo = os.getenv('GITHUB_REPO')
        if not repo:
            raise ValueError("GITHUB_REPO environment variable not set")
        return repo

    @property
    def github_token(self) -> Optional[str]:
        token = os.getenv('GITHUB_TOKEN', '').strip()
        return token if token else None

    @property
    def app_name(self) -> str:
        name = os.getenv('APP_NAME', 'MyApp')
        return name

    @property
    def include_pre_releases(self) -> bool:
        value = os.getenv('INCLUDE_PRE_RELEASES', 'false').lower()
        return value in ('true', '1', 'yes')

    @property
    def include_assets(self) -> bool:
        value = os.getenv('INCLUDE_ASSETS', 'true').lower()
        return value in ('true', '1', 'yes')
