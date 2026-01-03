"""
Utility module - General utility commands

Commands:
- !last <user> - When was user last seen
- !commands - List all commands
- !help [command] - Get help
- !ping - Check bot latency
- !uptime - Bot uptime
- !random - Execute a random command
"""

import json
import os
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.registry import command, CommandContext, registry
from core.permissions import PermissionLevel, get_user_level
from config import config, DATA_DIR


LAST_SEEN_FILE = DATA_DIR / "last_seen.json"


def load_last_seen() -> dict:
    """Load last seen data"""
    if not LAST_SEEN_FILE.exists():
        return {}
    
    try:
        return json.loads(LAST_SEEN_FILE.read_text())
    except:
        return {}


def save_last_seen(data: dict):
    """Save last seen data"""
    LAST_SEEN_FILE.write_text(json.dumps(data, indent=2))


def update_last_seen(username: str):
    """Update a user's last seen timestamp"""
    data = load_last_seen()
    data[username.lower()] = datetime.now().isoformat()
    save_last_seen(data)


def get_last_seen(username: str) -> Optional[datetime]:
    """Get when a user was last seen"""
    data = load_last_seen()
    timestamp = data.get(username.lower())
    
    if timestamp:
        try:
            return datetime.fromisoformat(timestamp)
        except:
            pass
    
    return None


def format_time_ago(dt: datetime) -> str:
    """Format a datetime as 'X ago' string"""
    delta = datetime.now() - dt
    
    seconds = int(delta.total_seconds())
    
    if seconds < 60:
        return f"{seconds} seconds ago"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = seconds // 86400
        return f"{days} day{'s' if days != 1 else ''} ago"


@command(
    "last",
    description="Check when a user was last seen",
    usage="!last <username>",
    aliases=["lastseen", "seen"],
)
def cmd_last(ctx: CommandContext, args: str):
    """Check when a user was last seen"""
    if not args.strip():
        ctx.reply("Usage: !last <username>")
        return
    
    target = args.split()[0].lstrip("@").lower()
    last_seen = get_last_seen(target)
    
    if last_seen:
        time_ago = format_time_ago(last_seen)
        formatted = last_seen.strftime("%b %d, %Y at %I:%M %p")
        ctx.reply(f"👤 {target} was last seen {time_ago} ({formatted})")
    else:
        ctx.reply(f"👤 {target} has never been seen")


@command(
    "commands",
    description="Get the link to the command list",
    usage="!commands",
    aliases=["cmds", "commandlist"],
)
def cmd_commands(ctx: CommandContext, args: str):
    """Link to the full command list spreadsheet"""
    # Check if spreadsheet URL is configured
    spreadsheet_url = os.getenv("COMMANDS_SPREADSHEET_URL", "")
    
    if spreadsheet_url:
        ctx.reply(f"Command list: {spreadsheet_url}")
    else:
        # Fallback to listing commands in chat
        user_level = get_user_level(ctx.user.username)
        commands = registry.list_commands(permission_level=user_level)
        
        # Group by module
        modules = {}
        for cmd in commands:
            module = cmd.module or "other"
            if module not in modules:
                modules[module] = []
            modules[module].append(cmd.name)
        
        parts = []
        for module, cmds in sorted(modules.items()):
            cmd_list = ", ".join([f"!{c}" for c in sorted(cmds)[:5]])
            if len(cmds) > 5:
                cmd_list += f"... (+{len(cmds)-5} more)"
            parts.append(f"[{module}] {cmd_list}")
        
        ctx.reply(f"Commands: {' | '.join(parts)}")


@command(
    "help",
    description="Get help for a command",
    usage="!help [command]",
    aliases=["h", "?"],
)
def cmd_help(ctx: CommandContext, args: str):
    """Get help for a command or general help"""
    if not args.strip():
        # General help
        ctx.reply(
            f"🤖 {config.BOT_DISPLAY_NAME} - Use !commands to see all commands, "
            f"!help <command> for specific help"
        )
        return
    
    cmd_name = args.split()[0].lower().lstrip("!")
    cmd_info = registry.get_command(cmd_name)
    
    if not cmd_info:
        # Check custom commands
        from modules.custom_commands import get_custom_command
        custom = get_custom_command(cmd_name)
        if custom:
            ctx.reply(f"!{cmd_name} - Custom command")
            return
        
        ctx.reply(f"Command !{cmd_name} not found")
        return
    
    # Build help message
    parts = [f"!{cmd_info.name}"]
    
    if cmd_info.aliases:
        parts.append(f"(aliases: {', '.join(['!' + a for a in cmd_info.aliases])})")
    
    if cmd_info.description:
        parts.append(f"- {cmd_info.description}")
    
    if cmd_info.usage:
        parts.append(f"Usage: {cmd_info.usage}")
    
    ctx.reply(" ".join(parts))


@command(
    "ping",
    description="Check if the bot is responsive",
    usage="!ping",
)
def cmd_ping(ctx: CommandContext, args: str):
    """Ping the bot"""
    ctx.reply("🏓 Pong!")


@command(
    "uptime",
    description="Show bot uptime",
    usage="!uptime",
)
def cmd_uptime(ctx: CommandContext, args: str):
    """Show bot uptime"""
    uptime_seconds = ctx.bot.uptime
    
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    ctx.reply(f"⏱️ Uptime: {' '.join(parts)}")


@command(
    "stats",
    description="Show bot statistics",
    usage="!stats",
)
def cmd_stats(ctx: CommandContext, args: str):
    """Show bot statistics"""
    stats = ctx.bot.stats
    
    ctx.reply(
        f"📊 Stats: {stats['messages_processed']} messages, "
        f"{stats['commands_processed']} commands, "
        f"{stats['online_users']} online, "
        f"{stats['reconnects']} reconnects"
    )


@command(
    "random",
    description="Execute a random command",
    usage="!random",
    aliases=["rand"],
)
def cmd_random(ctx: CommandContext, args: str):
    """Execute a random custom command"""
    from modules.custom_commands import load_custom_commands
    
    commands = load_custom_commands()
    
    if not commands:
        ctx.reply("No custom commands available!")
        return
    
    cmd_name = random.choice(list(commands.keys()))
    response = commands[cmd_name]  # commands are stored as simple strings, not dicts
    
    ctx.reply(f"[!{cmd_name}] {response}")


@command(
    "about",
    description="About the bot",
    usage="!about",
)
def cmd_about(ctx: CommandContext, args: str):
    """Show bot information"""
    ctx.reply(
        f"🤖 {config.BOT_DISPLAY_NAME} - Manestream Chat Bot | "
        f"Features: Fishing, BongBux, Gambling, Custom Commands | "
        f"Use !help for more info"
    )


def setup(bot):
    """Module setup - track user activity"""
    
    def track_activity(bot_client, message):
        """Track when users are active"""
        update_last_seen(message.user.username)
        return None  # Continue processing
    
    bot.on_message_handlers.append(track_activity)
    
    # Load existing data
    data = load_last_seen()
    print(f"    👥 Tracking {len(data)} users")


def teardown(bot):
    """Module teardown"""
    pass
