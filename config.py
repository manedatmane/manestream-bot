"""
Configuration management for Manestream Bot
"""

import os
import json
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

# Ensure data directories exist
DIRS_TO_CREATE = [
    DATA_DIR,
    DATA_DIR / "bongbux",
    DATA_DIR / "fish",
    DATA_DIR / "logs",
]

for dir_path in DIRS_TO_CREATE:
    dir_path.mkdir(parents=True, exist_ok=True)


class Config:
    """Bot configuration - loads from environment and config file"""
    
    def __init__(self):
        # Connection settings
        self.CHAT_SERVER_URL = os.getenv("CHAT_SERVER_URL", "http://localhost:3000")
        self.BOT_API_KEY = os.getenv("BOT_API_KEY", "dev-bot-key-12345")
        
        # Bot identity
        self.BOT_USERNAME = os.getenv("BOT_USERNAME", "FishBot")
        self.BOT_DISPLAY_NAME = os.getenv("BOT_DISPLAY_NAME", "🐟 FishBot")
        self.BOT_AVATAR = os.getenv("BOT_AVATAR", "")
        
        # Admin users (can use admin commands)
        admin_str = os.getenv("ADMIN_USERS", "bong,saiyajin,north")
        self.ADMIN_USERS = [u.strip().lower() for u in admin_str.split(",") if u.strip()]
        
        # Game settings
        self.STARTING_BONGBUX = int(os.getenv("STARTING_BONGBUX", "5000"))
        self.FISH_COOLDOWN = int(os.getenv("FISH_COOLDOWN", "30"))
        self.GAMBLE_WIN_RATE = float(os.getenv("GAMBLE_WIN_RATE", "0.45"))
        
        # Message settings
        self.MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "500"))
        self.COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
        
        # API keys (optional)
        self.GIPHY_API_KEY = os.getenv("GIPHY_API_KEY", "")
        self.TENOR_API_KEY = os.getenv("TENOR_API_KEY", "")
        self.OMDB_API_KEY = os.getenv("OMDB_API_KEY", "")
        
        # Reconnection settings
        self.RECONNECT_DELAY = int(os.getenv("RECONNECT_DELAY", "5"))
        self.MAX_RECONNECT_DELAY = int(os.getenv("MAX_RECONNECT_DELAY", "60"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Enabled modules
        self.ENABLED_MODULES = [
            "economy",
            "fishing", 
            "gambling",
            "custom_commands",
            "moderation",
            "api_commands",
            "utility",
            "fun",
        ]
        
        # Load runtime config overrides
        self._load_runtime_config()
    
    def _load_runtime_config(self):
        """Load runtime config from JSON file"""
        config_file = DATA_DIR / "config.json"
        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    runtime = json.load(f)
                    
                # Override with runtime values
                if "fish_cooldown" in runtime:
                    self.FISH_COOLDOWN = runtime["fish_cooldown"]
                if "starting_bongbux" in runtime:
                    self.STARTING_BONGBUX = runtime["starting_bongbux"]
                if "gamble_win_rate" in runtime:
                    self.GAMBLE_WIN_RATE = runtime["gamble_win_rate"]
                if "enabled_modules" in runtime:
                    self.ENABLED_MODULES = runtime["enabled_modules"]
                    
            except Exception as e:
                print(f"Warning: Could not load runtime config: {e}")
    
    def save_runtime_config(self):
        """Save current runtime config to JSON"""
        config_file = DATA_DIR / "config.json"
        runtime = {
            "fish_cooldown": self.FISH_COOLDOWN,
            "starting_bongbux": self.STARTING_BONGBUX,
            "gamble_win_rate": self.GAMBLE_WIN_RATE,
            "enabled_modules": self.ENABLED_MODULES,
        }
        with open(config_file, "w") as f:
            json.dump(runtime, f, indent=2)
    
    def is_admin(self, username: str) -> bool:
        """Check if user is an admin"""
        return username.lower() in self.ADMIN_USERS


# Global config instance
config = Config()
