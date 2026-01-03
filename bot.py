#!/usr/bin/env python3
"""
Manestream Bot - Main Entry Point

A modular chat bot for the Manestream Chat system.

Usage:
    python bot.py                  # Run normally
    python bot.py --production     # Run with production settings
    python bot.py --debug          # Run with debug logging
"""

import sys
import os
import argparse
import logging

# Load environment variables from .env file BEFORE importing config
# This is crucial - must happen before config.py is imported
from pathlib import Path

# Try multiple possible locations for .env
script_dir = Path(__file__).parent.resolve()
possible_env_files = [
    script_dir / ".env",
    Path.cwd() / ".env",
    script_dir / "_env",  # In case Windows hid the dot
]

env_loaded = False
for env_file in possible_env_files:
    if env_file.exists():
        print(f"Found .env at: {env_file}")
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, override=True)
            env_loaded = True
            print(f"Loaded .env using python-dotenv")
        except ImportError:
            # Manual .env loading if dotenv not installed
            print("python-dotenv not installed, loading .env manually...")
            with open(env_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        # Remove quotes if present
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]
                        os.environ[key] = value
            env_loaded = True
            print(f"Loaded .env manually")
        break

if not env_loaded:
    print(f"WARNING: No .env file found!")
    print(f"Searched in: {[str(p) for p in possible_env_files]}")
    print(f"Using default/environment values")

# Debug: Show what we loaded
print(f"\nEnvironment check:")
print(f"  GIPHY_API_KEY in env: {'yes' if os.environ.get('GIPHY_API_KEY') else 'no'}")
print(f"  TENOR_API_KEY in env: {'yes' if os.environ.get('TENOR_API_KEY') else 'no'}")
print(f"  OMDB_API_KEY in env: {'yes' if os.environ.get('OMDB_API_KEY') else 'no'}")

# Now import config (it will read from os.environ)
from config import config
from core.client import BotClient
from core.registry import registry
from modules import load_modules


def setup_logging(debug: bool = False):
    """Configure logging"""
    level = logging.DEBUG if debug else getattr(logging, config.LOG_LEVEL)
    
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Manestream Chat Bot")
    parser.add_argument("--production", action="store_true", help="Run in production mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(debug=args.debug)
    
    print("")
    print("=" * 58)
    print(f"  {config.BOT_DISPLAY_NAME}")
    print("=" * 58)
    print(f"  Server: {config.CHAT_SERVER_URL}")
    print(f"  Mode: {'Production' if args.production else 'Development'}")
    print("=" * 58)
    
    # Debug: Show API key status
    print("")
    print("API Keys (from config):")
    print(f"  GIPHY: {'[' + config.GIPHY_API_KEY[:8] + '...]' if config.GIPHY_API_KEY else 'NOT SET'}")
    print(f"  Tenor: {'[' + config.TENOR_API_KEY[:8] + '...]' if config.TENOR_API_KEY else 'NOT SET'}")
    print(f"  OMDB:  {'[' + config.OMDB_API_KEY[:8] + '...]' if config.OMDB_API_KEY else 'NOT SET'}")
    print("")
    
    # Create bot client
    bot = BotClient()
    
    # Load modules
    print("Loading modules...")
    loaded, failed = load_modules(bot, config.ENABLED_MODULES)
    
    if failed:
        print("\n[WARN] Some modules failed to load:")
        for name, error in failed:
            print(f"  - {name}: {error}")
    
    print(f"\n{len(registry.commands)} commands registered")
    print("")
    
    # Run the bot
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
