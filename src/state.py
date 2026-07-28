import json
import os
from pathlib import Path
from typing import Any
from src.logger import logger

_data_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent))
_data_dir.mkdir(parents=True, exist_ok=True)
STATE_FILE = _data_dir / "state.json"

class StateManager:
    """Manages per-guild bot settings and release state."""

    @staticmethod
    def _read_data() -> dict[str, Any]:
        try:
            if not STATE_FILE.exists():
                return {}
            with open(STATE_FILE, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
            return {}

    @staticmethod
    def _write_data(data: dict[str, Any]) -> bool:
        try:
            with open(STATE_FILE, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    @staticmethod
    def _get_guild_data(data: dict[str, Any], guild_id: int) -> dict[str, Any]:
        guilds = data.setdefault('guilds', {})
        return guilds.setdefault(str(guild_id), {})

    @staticmethod
    def get_guild_settings(guild_id: int) -> dict[str, Any]:
        """Return the configured settings for a guild."""
        data = StateManager._read_data()
        return data.get('guilds', {}).get(str(guild_id), {})

    @staticmethod
    def set_repository(guild_id: int, owner: str, repo: str, app_name: str) -> bool:
        """Set the GitHub repository and display name for a guild."""
        data = StateManager._read_data()
        guild = StateManager._get_guild_data(data, guild_id)
        guild['repository'] = {'owner': owner, 'repo': repo, 'app_name': app_name}
        return StateManager._write_data(data)

    @staticmethod
    def set_channel(guild_id: int, release_type: str, channel_id: int) -> bool:
        """Set the target channel for stable or beta releases."""
        data = StateManager._read_data()
        guild = StateManager._get_guild_data(data, guild_id)
        guild.setdefault('channels', {})[release_type] = channel_id
        return StateManager._write_data(data)

    @staticmethod
    def get_autopost_enabled(guild_id: int) -> bool:
        """Get the autopost state for a guild."""
        return StateManager.get_guild_settings(guild_id).get('autopost_enabled', False)

    @staticmethod
    def toggle_autopost(guild_id: int) -> bool:
        """Toggle autopost for a guild and return the new state."""
        data = StateManager._read_data()
        guild = StateManager._get_guild_data(data, guild_id)
        enabled = not guild.get('autopost_enabled', False)
        guild['autopost_enabled'] = enabled
        StateManager._write_data(data)
        return enabled

    @staticmethod
    def get_last_posted_release_id(guild_id: int, release_type: str) -> int:
        """Get the last posted release ID for a release type in a guild."""
        settings = StateManager.get_guild_settings(guild_id)
        return settings.get('last_posted_release_ids', {}).get(release_type, 0)

    @staticmethod
    def set_last_posted_release_id(guild_id: int, release_type: str, release_id: int) -> bool:
        """Store the last successfully posted release ID for a release type."""
        data = StateManager._read_data()
        guild = StateManager._get_guild_data(data, guild_id)
        guild.setdefault('last_posted_release_ids', {})[release_type] = release_id
        return StateManager._write_data(data)
