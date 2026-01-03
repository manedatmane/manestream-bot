"""
Custom commands module - ENHANCED for hidden URL embeds
Improved version that attempts to hide URLs when only media is posted

Key improvements:
1. For image/video URLs: Uses special formatting to minimize URL visibility
2. Handles long URLs by not truncating them
3. Improved embed detection for various media types
"""

import json
import os
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from core.registry import command, CommandContext, registry
from core.permissions import PermissionLevel
from config import config, DATA_DIR


CUSTOM_COMMANDS_FILE = DATA_DIR / "custom_commands.json"

# Google Sheets configuration
SHEETS_ENABLED = False
sheets_sync = None

try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


def is_image_url(url: str) -> bool:
    """
    Check if a URL points to an image
    """
    url_lower = url.lower()
    
    # Check for direct image extensions
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
    if any(url_lower.endswith(ext) for ext in image_extensions):
        return True
    
    # Check for image hosting services that auto-embed
    image_hosts = [
        'i.imgur.com',
        'media.giphy.com',
        'media4.giphy.com',
        'media1.giphy.com',
        'media2.giphy.com',
        'media3.giphy.com',
        'tenor.com/view',
        'i.redd.it',
        'pbs.twimg.com',
        'i.pinimg.com',
        'cdn.discordapp.com/attachments',
    ]
    
    return any(host in url_lower for host in image_hosts)


def is_video_url(url: str) -> bool:
    """Check if a URL points to a video or video platform"""
    url_lower = url.lower()
    
    video_platforms = [
        'youtube.com',
        'youtu.be',
        'streamable.com',
        'twitch.tv',
        'clips.twitch.tv',
        'vimeo.com',
    ]
    
    return any(platform in url_lower for platform in video_platforms)


def extract_urls(text: str) -> list:
    """Extract all URLs from text"""
    url_pattern = r'https?://[^\s]+'
    return re.findall(url_pattern, text)


def format_media_only_message(url: str, media_type: str = "image") -> str:
    """
    Format a message to minimize URL visibility for media-only commands
    
    Options tried:
    1. Just URL - shows URL + embed (current problem)
    2. URL in brackets [url] - might hide it in some clients
    3. URL with label [label](url) - markdown style (if supported)
    
    Since Manestream doesn't seem to support hiding URLs via formatting,
    we'll just send the URL cleanly and let the user decide if they want
    to add additional formatting in the command itself.
    """
    # For now, just return the URL as-is
    # The chat client will handle the embedding
    return url


def send_smart_message(bot_client, response: str):
    """
    Send a message with smart handling of URLs and embeds
    
    Important: Since Manestream chat shows both URL and embed,
    this version focuses on:
    1. Not truncating URLs (send them complete)
    2. Proper message splitting if needed
    """
    response = response.strip()
    
    # Extract URLs
    urls = extract_urls(response)
    
    # Case 1: Response is ONLY a URL
    if len(urls) == 1 and response.replace(urls[0], '').strip() == '':
        url = urls[0]
        
        # Detect media type
        if is_image_url(url):
            formatted = format_media_only_message(url, "image")
        elif is_video_url(url):
            formatted = format_media_only_message(url, "video")
        else:
            formatted = url
        
        bot_client.send_message(formatted)
        return
    
    # Case 2: Response contains URLs but also has other text
    max_length = config.MAX_MESSAGE_LENGTH
    
    if len(response) <= max_length:
        bot_client.send_message(response)
    else:
        # Split intelligently while keeping URLs intact
        parts = []
        current_part = ""
        words = response.split()
        
        for word in words:
            test_length = len(current_part) + len(word) + (1 if current_part else 0)
            
            if test_length <= max_length:
                current_part += (" " if current_part else "") + word
            else:
                if current_part:
                    parts.append(current_part)
                current_part = word
        
        if current_part:
            parts.append(current_part)
        
        # Send each part
        for part in parts:
            bot_client.send_message(part)
            time.sleep(0.3)


class GoogleSheetsSync:
    """Handles syncing commands to Google Sheets"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.sheet = None
        self.enabled = False
        self.client = None
        
        if GSPREAD_AVAILABLE and os.path.exists(credentials_file):
            try:
                self._setup_connection()
                self.enabled = True
                print("    [OK] Google Sheets integration enabled")
            except Exception as e:
                print(f"    [ERR] Google Sheets setup failed: {e}")
    
    def _setup_connection(self):
        """Set up connection to Google Sheets"""
        scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ]
        creds = Credentials.from_service_account_file(self.credentials_file, scopes=scope)
        self.client = gspread.authorize(creds)
        self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
    
    def categorize_command(self, command_name: str, response: str) -> str:
        """Categorize a command based on its response"""
        if not response or response.strip() == "":
            return "Text"
        
        urls = extract_urls(response)
        if urls:
            url = urls[0]
            if is_image_url(url):
                return "Image"
            elif is_video_url(url):
                return "Video"
            elif "vocaroo.com" in url:
                return "Audio"
            else:
                return "Link"
        else:
            return "Text"
    
    def sync_all_commands(self, commands_dict: Dict[str, str]) -> bool:
        """Sync all commands to Google Sheets"""
        if not self.enabled:
            return False
        
        try:
            self.sheet.clear()
            time.sleep(0.2)
            
            headers = ['Command Name', 'URL/Response', 'Type', 'Description', 'Last Updated']
            self.sheet.append_row(headers)
            time.sleep(0.2)
            
            try:
                self.sheet.format('A1:E1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
            except Exception:
                pass
            
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            all_rows = []
            
            for cmd_name, response in sorted(commands_dict.items()):
                cmd_type = self.categorize_command(cmd_name, response)
                description = f"{cmd_type} command"
                all_rows.append([f"!{cmd_name}", response, cmd_type, description, current_time])
            
            batch_size = 50
            for i in range(0, len(all_rows), batch_size):
                batch = all_rows[i:i + batch_size]
                start_row = i + 2
                end_row = start_row + len(batch) - 1
                
                try:
                    self.sheet.update(f"A{start_row}:E{end_row}", batch)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"    [ERR] Batch update failed: {e}")
            
            print(f"    [OK] Synced {len(commands_dict)} commands to Google Sheets")
            return True
            
        except Exception as e:
            print(f"    [ERR] Sync failed: {e}")
            return False
    
    def add_command_to_sheet(self, cmd_name: str, response: str) -> bool:
        """Add a single command to the sheet"""
        if not self.enabled:
            return False
        
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cmd_type = self.categorize_command(cmd_name, response)
            description = f"{cmd_type} command"
            self.sheet.append_row([f"!{cmd_name}", response, cmd_type, description, current_time])
            return True
        except Exception as e:
            print(f"    [ERR] Failed to add command to sheet: {e}")
            return False
    
    def remove_command_from_sheet(self, cmd_name: str) -> bool:
        """Remove a command from the sheet"""
        if not self.enabled:
            return False
        
        try:
            cell = self.sheet.find(f"!{cmd_name}")
            if cell:
                self.sheet.delete_rows(cell.row)
                return True
        except Exception as e:
            print(f"    [ERR] Failed to remove command from sheet: {e}")
        return False
    
    def update_command_in_sheet(self, cmd_name: str, response: str) -> bool:
        """Update an existing command in the sheet"""
        if not self.enabled:
            return False
        
        try:
            cell = self.sheet.find(f"!{cmd_name}")
            if cell:
                row = cell.row
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cmd_type = self.categorize_command(cmd_name, response)
                self.sheet.update(f"B{row}:E{row}", [[response, cmd_type, f"{cmd_type} command", current_time]])
                return True
        except Exception as e:
            print(f"    [ERR] Failed to update command in sheet: {e}")
        return False
    
    def get_sheet_url(self) -> str:
        """Get the URL to the Google Sheet"""
        return f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit"


def load_custom_commands() -> Dict[str, str]:
    """Load custom commands from file"""
    if not CUSTOM_COMMANDS_FILE.exists():
        return {}
    
    try:
        data = json.loads(CUSTOM_COMMANDS_FILE.read_text())
        normalized = {}
        for name, value in data.items():
            if isinstance(value, str):
                normalized[name] = value
            elif isinstance(value, dict) and "response" in value:
                normalized[name] = value["response"]
            else:
                normalized[name] = str(value)
        return normalized
    except (json.JSONDecodeError, IOError):
        return {}


def save_custom_commands(commands: Dict[str, str]):
    """Save custom commands to file"""
    CUSTOM_COMMANDS_FILE.write_text(json.dumps(commands, indent=2))


def get_custom_command(name: str) -> Optional[str]:
    """Get a custom command by name"""
    commands = load_custom_commands()
    return commands.get(name.lower())


def add_custom_command(name: str, response: str) -> bool:
    """Add a custom command. Returns True if added, False if already exists"""
    commands = load_custom_commands()
    name = name.lower()
    
    if name in commands:
        return False
    
    commands[name] = response
    save_custom_commands(commands)
    
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.add_command_to_sheet(name, response)
    
    return True


def delete_custom_command(name: str) -> bool:
    """Delete a custom command. Returns True if deleted, False if not found"""
    commands = load_custom_commands()
    name = name.lower()
    
    if name not in commands:
        return False
    
    del commands[name]
    save_custom_commands(commands)
    
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.remove_command_from_sheet(name)
    
    return True


def edit_custom_command(name: str, response: str) -> bool:
    """Edit an existing custom command. Returns True if edited, False if not found"""
    commands = load_custom_commands()
    name = name.lower()
    
    if name not in commands:
        return False
    
    commands[name] = response
    save_custom_commands(commands)
    
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.update_command_in_sheet(name, response)
    
    return True


@command(
    "addcmd",
    description="Create a custom command",
    usage="!addcmd <n> <response>",
    aliases=["newcmd", "createcmd"],
)
def cmd_addcmd(ctx: CommandContext, args: str):
    """Add a new custom command"""
    parts = args.split(maxsplit=1)
    
    if len(parts) < 2:
        ctx.reply("Usage: !addcmd <n> <response>")
        return
    
    name = parts[0].lower().lstrip("!")
    response = parts[1]
    
    if registry.get_command(name):
        ctx.reply(f"!{name} is a built-in command and can't be overwritten")
        return
    
    if len(name) > 32:
        ctx.reply("Command name too long (max 32 characters)")
        return
    
    # Increased limit for URLs (they can be very long)
    max_response_length = 1500
    if len(response) > max_response_length:
        ctx.reply(f"Response too long (max {max_response_length} characters)")
        return
    
    if add_custom_command(name, response):
        ctx.reply(f"✅ Command !{name} added")
    else:
        ctx.reply(f"❌ Command !{name} already exists")


@command(
    "delcmd",
    description="Delete a custom command",
    usage="!delcmd <n>",
    aliases=["removecmd", "rmcmd"],
    admin=True,
)
def cmd_delcmd(ctx: CommandContext, args: str):
    """Delete a custom command (admin only)"""
    if not args.strip():
        ctx.reply("Usage: !delcmd <n>")
        return
    
    name = args.split()[0].lower().lstrip("!")
    
    if delete_custom_command(name):
        ctx.reply(f"✅ Command !{name} removed")
    else:
        ctx.reply(f"❌ Command !{name} not found")


@command(
    "editcmd",
    description="Edit an existing custom command",
    usage="!editcmd <n> <new_response>",
    admin=True,
)
def cmd_editcmd(ctx: CommandContext, args: str):
    """Edit a custom command (admin only)"""
    parts = args.split(maxsplit=1)
    
    if len(parts) < 2:
        ctx.reply("Usage: !editcmd <n> <new_response>")
        return
    
    name = parts[0].lower().lstrip("!")
    response = parts[1]
    
    max_response_length = 1500
    if len(response) > max_response_length:
        ctx.reply(f"Response too long (max {max_response_length} characters)")
        return
    
    if edit_custom_command(name, response):
        ctx.reply(f"✅ Command !{name} updated")
    else:
        ctx.reply(f"❌ Command !{name} not found")


@command(
    "cmdinfo",
    description="Show info about a custom command",
    usage="!cmdinfo <n>",
)
def cmd_cmdinfo(ctx: CommandContext, args: str):
    """Show custom command info"""
    if not args.strip():
        ctx.reply("Usage: !cmdinfo <n>")
        return
    
    name = args.split()[0].lower().lstrip("!")
    response = get_custom_command(name)
    
    if not response:
        ctx.reply(f"❌ !{name} not found")
        return
    
    # Show more for URLs
    if extract_urls(response):
        display = response if len(response) <= 250 else response[:247] + "..."
    else:
        display = response if len(response) <= 100 else response[:97] + "..."
    
    # Add type indicator
    urls = extract_urls(response)
    if urls:
        url = urls[0]
        if is_image_url(url):
            type_indicator = "🖼️ Image"
        elif is_video_url(url):
            type_indicator = "🎥 Video"
        else:
            type_indicator = "🔗 Link"
    else:
        type_indicator = "💬 Text"
    
    ctx.reply(f"{type_indicator} !{name} → {display}")


@command(
    "commands",
    description="Get the link to the command list",
    usage="!commands",
    aliases=["cmds", "commandlist"],
)
def cmd_commands(ctx: CommandContext, args: str):
    """Link to the full command list"""
    if sheets_sync and sheets_sync.enabled:
        sheet_url = sheets_sync.get_sheet_url()
        ctx.reply(f"📋 Command list: {sheet_url}")
    else:
        spreadsheet_url = os.getenv("COMMANDS_SPREADSHEET_URL", "")
        if spreadsheet_url:
            ctx.reply(f"📋 Command list: {spreadsheet_url}")
        else:
            commands = load_custom_commands()
            if commands:
                cmd_list = ", ".join([f"!{c}" for c in sorted(commands.keys())[:20]])
                if len(commands) > 20:
                    ctx.reply(f"Custom commands ({len(commands)} total): {cmd_list}... (and {len(commands)-20} more)")
                else:
                    ctx.reply(f"Custom commands ({len(commands)}): {cmd_list}")
            else:
                ctx.reply("No custom commands yet! Use !addcmd to create one.")


@command(
    "syncsheet",
    description="Manually sync all commands to Google Sheets",
    usage="!syncsheet",
    admin=True,
)
def cmd_syncsheet(ctx: CommandContext, args: str):
    """Manually sync all commands to Google Sheets (admin only)"""
    if not sheets_sync or not sheets_sync.enabled:
        ctx.reply("❌ Google Sheets integration not available")
        return
    
    commands = load_custom_commands()
    ctx.reply(f"🔄 Syncing {len(commands)} commands...")
    
    if sheets_sync.sync_all_commands(commands):
        ctx.reply(f"✅ Sync complete! {sheets_sync.get_sheet_url()}")
    else:
        ctx.reply("❌ Sync failed - check console")


def setup(bot):
    """Module setup - register custom command handler and set up Google Sheets"""
    global sheets_sync, SHEETS_ENABLED
    
    credentials_file = DATA_DIR / "credentials.json"
    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", "1rbfLU0lJJ23q-WvuvQLg7gX1_59cPzrbuaYkwk97QEY")
    
    if GSPREAD_AVAILABLE and credentials_file.exists():
        sheets_sync = GoogleSheetsSync(str(credentials_file), spreadsheet_id)
        SHEETS_ENABLED = sheets_sync.enabled
    else:
        if not GSPREAD_AVAILABLE:
            print("    [WARN] gspread not installed")
        if not credentials_file.exists():
            print(f"    [WARN] No credentials.json found")
    
    # Message handler for custom commands
    def on_message(bot_client, message):
        content = message.content.strip()
        if content.startswith(config.COMMAND_PREFIX):
            if " " in content:
                cmd_part, args = content.split(" ", 1)
            else:
                cmd_part, args = content, ""
            
            cmd = cmd_part[len(config.COMMAND_PREFIX):].lower()
            
            if not registry.get_command(cmd):
                response = get_custom_command(cmd)
                if response:
                    send_smart_message(bot_client, response)
                    return False
        return None
    
    bot.on_message_handlers.append(on_message)
    
    commands = load_custom_commands()
    print(f"    {len(commands)} custom commands loaded")


def teardown(bot):
    """Module teardown"""
    pass