import json
import os
from pathlib import Path
from src.logger import logger

_data_dir = Path(os.getenv("DATA_DIR", Path(__file__).parent.parent))
_data_dir.mkdir(parents=True, exist_ok=True)
STATE_FILE = _data_dir / "state.json"

class StateManager:
    """Manages bot state and settings"""

    @staticmethod
    def get_autopost_enabled() -> bool:
        """Get autopost enabled state"""
        try:
            if not STATE_FILE.exists():
                return False
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('autopost_enabled', False)
        except Exception as e:
            logger.error(f"Failed to read state: {e}")
            return False

    @staticmethod
    def set_autopost_enabled(enabled: bool) -> bool:
        """Set autopost enabled state"""
        try:
            data = {}
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)

            data['autopost_enabled'] = enabled

            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Autopost set to: {enabled}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    @staticmethod
    def toggle_autopost() -> bool:
        """Toggle autopost state and return new state"""
        current = StateManager.get_autopost_enabled()
        new_state = not current
        StateManager.set_autopost_enabled(new_state)
        return new_state

    @staticmethod
    def get_last_posted_release_id() -> int:
        """Get the ID of the last posted release"""
        try:
            if not STATE_FILE.exists():
                return 0
            with open(STATE_FILE, 'r') as f:
                data = json.load(f)
                return data.get('last_posted_release_id', 0)
        except Exception as e:
            logger.error(f"Failed to read last posted release ID: {e}")
            return 0

    @staticmethod
    def set_last_posted_release_id(release_id: int) -> bool:
        """Set the ID of the last posted release"""
        try:
            data = {}
            if STATE_FILE.exists():
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)

            data['last_posted_release_id'] = release_id

            with open(STATE_FILE, 'w') as f:
                json.dump(data, f, indent=2)

            logger.info(f"Last posted release ID set to: {release_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save last posted release ID: {e}")
            return False
