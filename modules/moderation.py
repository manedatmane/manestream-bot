"""
Moderation module - Ban management and auto-moderation

Commands:
- !ban <user> [reason] - Ban a user
- !unban <user> - Unban a user
- !banlist - Show banned users
- !mute <user> [duration] - Mute a user
- !unmute <user> - Unmute a user

Auto-moderation:
- Gibberish username detection
- Banned IP range checking
"""

import json
import re
import ipaddress
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional
import requests

from core.registry import command, CommandContext
from core.permissions import PermissionLevel
from config import config, DATA_DIR


BANS_FILE = DATA_DIR / "bans.json"
MUTES_FILE = DATA_DIR / "mutes.json"
BANNED_IPS_FILE = DATA_DIR / "banned_ip_ranges.txt"
BAN_LOG_FILE = DATA_DIR / "ban_log.json"


def load_bans() -> Dict:
    """Load ban list"""
    if not BANS_FILE.exists():
        return {"users": [], "ips": []}
    
    try:
        return json.loads(BANS_FILE.read_text())
    except:
        return {"users": [], "ips": []}


def save_bans(bans: Dict):
    """Save ban list"""
    BANS_FILE.write_text(json.dumps(bans, indent=2))


def load_mutes() -> Dict[str, str]:
    """Load mute list (username -> expiry timestamp)"""
    if not MUTES_FILE.exists():
        return {}
    
    try:
        return json.loads(MUTES_FILE.read_text())
    except:
        return {}


def save_mutes(mutes: Dict):
    """Save mute list"""
    MUTES_FILE.write_text(json.dumps(mutes, indent=2))


def load_banned_ip_ranges() -> List[ipaddress.IPv4Network]:
    """Load banned IP ranges from file"""
    if not BANNED_IPS_FILE.exists():
        return []
    
    networks = []
    try:
        for line in BANNED_IPS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                networks.append(ipaddress.ip_network(line, strict=False))
            except ValueError:
                pass
    except:
        pass
    
    return networks


def log_ban(username: str, banned_by: str, reason: str, ip: str = None):
    """Log a ban action"""
    logs = []
    if BAN_LOG_FILE.exists():
        try:
            logs = json.loads(BAN_LOG_FILE.read_text())
        except:
            pass
    
    logs.append({
        "username": username,
        "banned_by": banned_by,
        "reason": reason,
        "ip": ip,
        "timestamp": datetime.now().isoformat(),
    })
    
    # Keep last 1000 entries
    logs = logs[-1000:]
    BAN_LOG_FILE.write_text(json.dumps(logs, indent=2))


def is_gibberish_username(username: str) -> bool:
    """
    Detect gibberish usernames matching pattern: 6 letters + 4-5 digits
    Examples: cipey52636, licane7793, remom77689
    """
    if not username or username.startswith("!anon"):
        return False
    
    pattern = r'^[a-z]{6}\d{4,5}$'
    return bool(re.match(pattern, username.lower()))


def is_ip_banned(ip_str: str, networks: List) -> bool:
    """Check if IP is in banned ranges"""
    if not ip_str:
        return False
    
    try:
        ip = ipaddress.ip_address(ip_str)
        for network in networks:
            if ip in network:
                return True
    except ValueError:
        pass
    
    return False


def ban_user_via_api(identifier: str, ip: str = None) -> bool:
    """
    Ban a user via the chat server API
    
    Args:
        identifier: User identifier (e.g., "discord:123456")
        ip: Optional IP address to ban
        
    Returns:
        True if successful
    """
    try:
        response = requests.post(
            f"{config.CHAT_SERVER_URL}/api/ban",
            headers={"X-Admin-Key": config.BOT_API_KEY},
            json={"identifier": identifier, "ip": ip},
            timeout=5,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Ban API error: {e}")
        return False


def unban_user_via_api(identifier: str, ip: str = None) -> bool:
    """
    Unban a user via the chat server API
    
    Args:
        identifier: User identifier
        ip: Optional IP address to unban
        
    Returns:
        True if successful
    """
    try:
        response = requests.delete(
            f"{config.CHAT_SERVER_URL}/api/ban",
            headers={"X-Admin-Key": config.BOT_API_KEY},
            json={"identifier": identifier, "ip": ip},
            timeout=5,
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Unban API error: {e}")
        return False


@command(
    "ban",
    description="Ban a user from the chat",
    usage="!ban <username> [reason]",
    admin=True,
)
def cmd_ban(ctx: CommandContext, args: str):
    """Ban a user"""
    if not args.strip():
        ctx.reply("Usage: !ban <username> [reason]")
        return
    
    parts = args.split(maxsplit=1)
    target = parts[0].lstrip("@").lower()
    reason = parts[1] if len(parts) > 1 else "No reason given"
    
    # Add to local ban list
    bans = load_bans()
    if target not in bans["users"]:
        bans["users"].append(target)
        save_bans(bans)
    
    # Log the ban
    log_ban(target, ctx.user.username, reason)
    
    # Try to ban via API
    api_success = ban_user_via_api(target)
    
    if api_success:
        ctx.reply(f"🔨 Banned {target}: {reason}")
    else:
        ctx.reply(f"🔨 Banned {target} locally (API unavailable): {reason}")


@command(
    "unban",
    description="Unban a user",
    usage="!unban <username>",
    admin=True,
)
def cmd_unban(ctx: CommandContext, args: str):
    """Unban a user"""
    if not args.strip():
        ctx.reply("Usage: !unban <username>")
        return
    
    target = args.split()[0].lstrip("@").lower()
    
    # Remove from local ban list
    bans = load_bans()
    if target in bans["users"]:
        bans["users"].remove(target)
        save_bans(bans)
    
    # Try to unban via API
    api_success = unban_user_via_api(target)
    
    if api_success:
        ctx.reply(f"✅ Unbanned {target}")
    else:
        ctx.reply(f"✅ Unbanned {target} locally (API unavailable)")


@command(
    "banlist",
    description="Show banned users",
    usage="!banlist",
    admin=True,
)
def cmd_banlist(ctx: CommandContext, args: str):
    """Show banned users"""
    bans = load_bans()
    
    if not bans["users"]:
        ctx.reply("No users are banned")
        return
    
    # Limit display
    users = bans["users"][:20]
    user_list = ", ".join(users)
    
    if len(bans["users"]) > 20:
        ctx.reply(f"🚫 Banned ({len(bans['users'])} total): {user_list}... (showing first 20)")
    else:
        ctx.reply(f"🚫 Banned ({len(bans['users'])}): {user_list}")


@command(
    "mute",
    description="Mute a user",
    usage="!mute <username> [duration_minutes]",
    admin=True,
)
def cmd_mute(ctx: CommandContext, args: str):
    """Mute a user"""
    if not args.strip():
        ctx.reply("Usage: !mute <username> [duration_minutes]")
        return
    
    parts = args.split()
    target = parts[0].lstrip("@").lower()
    
    # Default 10 minute mute
    duration = 10
    if len(parts) > 1:
        try:
            duration = int(parts[1])
        except ValueError:
            pass
    
    # Calculate expiry
    from datetime import timedelta
    expiry = datetime.now() + timedelta(minutes=duration)
    
    mutes = load_mutes()
    mutes[target] = expiry.isoformat()
    save_mutes(mutes)
    
    ctx.reply(f"🔇 Muted {target} for {duration} minutes")


@command(
    "unmute",
    description="Unmute a user",
    usage="!unmute <username>",
    admin=True,
)
def cmd_unmute(ctx: CommandContext, args: str):
    """Unmute a user"""
    if not args.strip():
        ctx.reply("Usage: !unmute <username>")
        return
    
    target = args.split()[0].lstrip("@").lower()
    
    mutes = load_mutes()
    if target in mutes:
        del mutes[target]
        save_mutes(mutes)
        ctx.reply(f"🔊 Unmuted {target}")
    else:
        ctx.reply(f"{target} is not muted")


def is_user_muted(username: str) -> bool:
    """Check if user is currently muted"""
    mutes = load_mutes()
    
    if username.lower() not in mutes:
        return False
    
    expiry_str = mutes[username.lower()]
    try:
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.now() >= expiry:
            # Mute expired, remove it
            del mutes[username.lower()]
            save_mutes(mutes)
            return False
        return True
    except:
        return False


# Auto-moderation state
_banned_ip_networks = []
_recent_auto_bans: Set[str] = set()


def setup(bot):
    """Module setup - initialize auto-moderation"""
    global _banned_ip_networks
    
    # Load banned IP ranges
    _banned_ip_networks = load_banned_ip_ranges()
    print(f"    🛡️ Loaded {len(_banned_ip_networks)} banned IP ranges")
    
    # Add message handler for auto-moderation
    def automod_handler(bot_client, message):
        username = message.user.username
        
        # Check mute
        if is_user_muted(username):
            # In a real implementation, we'd delete the message
            # For now, just log it
            print(f"🔇 Blocked muted user: {username}")
            return False
        
        # Check gibberish username
        if is_gibberish_username(username):
            print(f"🚨 Detected gibberish username: {username}")
            # Auto-ban via API
            ban_user_via_api(username)
            log_ban(username, "AutoMod", "Gibberish username pattern")
            return False
        
        return None
    
    bot.on_message_handlers.insert(0, automod_handler)  # Run first
    
    # Load bans
    bans = load_bans()
    print(f"    🚫 {len(bans['users'])} users banned")


def teardown(bot):
    """Module teardown"""
    pass
