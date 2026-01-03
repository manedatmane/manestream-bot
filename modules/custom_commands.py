"""
Custom commands module - User-defined text commands with Google Sheets sync

Commands:
- !addcmd <name> <response> - Create a custom command
- !delcmd <name> - Delete a custom command (admin only)
- !editcmd <name> <response> - Edit a custom command (admin only)
- !cmdinfo <name> - Show info about a custom command
- !commands - Link to Google Sheets command list
- !syncsheet - Manually sync all commands to Google Sheets (admin only)
"""

import json
import os
import time
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
        
        # Open by spreadsheet ID
        self.sheet = self.client.open_by_key(self.spreadsheet_id).sheet1
    
    def categorize_command(self, command_name: str, response: str) -> str:
        """Categorize a command based on its response"""
        if not response or response.strip() == "":
            return "Text"
        elif "youtube.com" in response or "youtu.be" in response:
            return "Video"
        elif any(ext in response.lower() for ext in ['.gif', '.jpg', '.jpeg', '.png', '.webp']):
            return "Image"
        elif "streamable.com" in response or "vocaroo.com" in response:
            return "Media"
        elif response.startswith("http"):
            return "Link"
        else:
            return "Text"
    
    def sync_all_commands(self, commands_dict: Dict[str, str]) -> bool:
        """Sync all commands to Google Sheets"""
        if not self.enabled:
            return False
        
        try:
            # Clear existing data
            self.sheet.clear()
            time.sleep(0.2)
            
            # Add headers
            headers = ['Command Name', 'URL/Response', 'Type', 'Description', 'Last Updated']
            self.sheet.append_row(headers)
            time.sleep(0.2)
            
            # Format headers (bold, gray background)
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
                
                # Truncate very long responses
                display_response = response if len(response) <= 500 else response[:497] + "..."
                
                all_rows.append([f"!{cmd_name}", display_response, cmd_type, description, current_time])
            
            # Batch update in chunks of 50
            batch_size = 50
            for i in range(0, len(all_rows), batch_size):
                batch = all_rows[i:i + batch_size]
                start_row = i + 2
                end_row = start_row + len(batch) - 1
                
                try:
                    self.sheet.update(f"A{start_row}:E{end_row}", batch)
                    time.sleep(0.5)  # Rate limiting
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
            display_response = response if len(response) <= 500 else response[:497] + "..."
            
            self.sheet.append_row([f"!{cmd_name}", display_response, cmd_type, description, current_time])
            return True
        except Exception as e:
            print(f"    [ERR] Failed to add command to sheet: {e}")
            return False
    
    def remove_command_from_sheet(self, cmd_name: str) -> bool:
        """Remove a command from the sheet"""
        if not self.enabled:
            return False
        
        try:
            # Find the row with this command
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
                display_response = response if len(response) <= 500 else response[:497] + "..."
                
                self.sheet.update(f"B{row}:E{row}", [[display_response, cmd_type, f"{cmd_type} command", current_time]])
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
        # Handle both old format (just response) and new format (with metadata)
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
    """
    Add a custom command
    
    Returns:
        True if added, False if already exists
    """
    commands = load_custom_commands()
    name = name.lower()
    
    if name in commands:
        return False
    
    commands[name] = response
    save_custom_commands(commands)
    
    # Sync to Google Sheets
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.add_command_to_sheet(name, response)
    
    return True


def delete_custom_command(name: str) -> bool:
    """
    Delete a custom command
    
    Returns:
        True if deleted, False if not found
    """
    commands = load_custom_commands()
    name = name.lower()
    
    if name not in commands:
        return False
    
    del commands[name]
    save_custom_commands(commands)
    
    # Remove from Google Sheets
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.remove_command_from_sheet(name)
    
    return True


def edit_custom_command(name: str, response: str) -> bool:
    """
    Edit an existing custom command
    
    Returns:
        True if edited, False if not found
    """
    commands = load_custom_commands()
    name = name.lower()
    
    if name not in commands:
        return False
    
    commands[name] = response
    save_custom_commands(commands)
    
    # Update in Google Sheets
    if sheets_sync and sheets_sync.enabled:
        sheets_sync.update_command_in_sheet(name, response)
    
    return True


@command(
    "addcmd",
    description="Create a custom command",
    usage="!addcmd <name> <response>",
    aliases=["newcmd", "createcmd"],
)
def cmd_addcmd(ctx: CommandContext, args: str):
    """Add a new custom command"""
    parts = args.split(maxsplit=1)
    
    if len(parts) < 2:
        ctx.reply("Usage: !addcmd <name> <response>")
        return
    
    name = parts[0].lower().lstrip("!")
    response = parts[1]
    
    # Check if name conflicts with built-in commands
    if registry.get_command(name):
        ctx.reply(f"!{name} is a built-in command and can't be overwritten")
        return
    
    # Check length limits
    if len(name) > 32:
        ctx.reply("Command name too long (max 32 characters)")
        return
    
    if len(response) > 500:
        ctx.reply("Response too long (max 500 characters)")
        return
    
    if add_custom_command(name, response):
        ctx.reply(f"Command !{name} has been added successfully")
    else:
        ctx.reply(f"Command !{name} already exists")


@command(
    "delcmd",
    description="Delete a custom command",
    usage="!delcmd <name>",
    aliases=["removecmd", "rmcmd"],
    admin=True,
)
def cmd_delcmd(ctx: CommandContext, args: str):
    """Delete a custom command (admin only)"""
    if not args.strip():
        ctx.reply("Usage: !delcmd <name>")
        return
    
    name = args.split()[0].lower().lstrip("!")
    
    if delete_custom_command(name):
        ctx.reply(f"Command !{name} has been removed")
    else:
        ctx.reply(f"Command !{name} not found")


@command(
    "editcmd",
    description="Edit an existing custom command",
    usage="!editcmd <name> <new_response>",
    admin=True,
)
def cmd_editcmd(ctx: CommandContext, args: str):
    """Edit a custom command (admin only)"""
    parts = args.split(maxsplit=1)
    
    if len(parts) < 2:
        ctx.reply("Usage: !editcmd <name> <new_response>")
        return
    
    name = parts[0].lower().lstrip("!")
    response = parts[1]
    
    if len(response) > 500:
        ctx.reply("Response too long (max 500 characters)")
        return
    
    if edit_custom_command(name, response):
        ctx.reply(f"Command !{name} has been updated")
    else:
        ctx.reply(f"Command !{name} not found")


@command(
    "cmdinfo",
    description="Show info about a custom command",
    usage="!cmdinfo <name>",
)
def cmd_cmdinfo(ctx: CommandContext, args: str):
    """Show custom command info"""
    if not args.strip():
        ctx.reply("Usage: !cmdinfo <name>")
        return
    
    name = args.split()[0].lower().lstrip("!")
    response = get_custom_command(name)
    
    if not response:
        ctx.reply(f"!{name} not found")
        return
    
    # Truncate response for display
    display = response if len(response) <= 100 else response[:97] + "..."
    ctx.reply(f"!{name} -> {display}")


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
        ctx.reply(f"View all commands here: {sheet_url}")
    else:
        # Fallback to env variable URL
        spreadsheet_url = os.getenv("COMMANDS_SPREADSHEET_URL", "")
        if spreadsheet_url:
            ctx.reply(f"View all commands here: {spreadsheet_url}")
        else:
            # List commands in chat
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
        ctx.reply("Google Sheets integration is not available. Need credentials.json and GOOGLE_SHEET_ID")
        return
    
    commands = load_custom_commands()
    ctx.reply(f"Starting sync of {len(commands)} commands...")
    
    if sheets_sync.sync_all_commands(commands):
        ctx.reply(f"Sync completed! View at: {sheets_sync.get_sheet_url()}")
    else:
        ctx.reply("Sync failed - check console for details")


def setup(bot):
    """Module setup - register custom command handler and set up Google Sheets"""
    global sheets_sync, SHEETS_ENABLED
    
    # Initialize Google Sheets if credentials exist
    credentials_file = DATA_DIR / "credentials.json"
    spreadsheet_id = os.getenv("GOOGLE_SHEET_ID", "1rbfLU0lJJ23q-WvuvQLg7gX1_59cPzrbuaYkwk97QEY")
    
    if GSPREAD_AVAILABLE and credentials_file.exists():
        sheets_sync = GoogleSheetsSync(str(credentials_file), spreadsheet_id)
        SHEETS_ENABLED = sheets_sync.enabled
    else:
        if not GSPREAD_AVAILABLE:
            print("    [WARN] gspread not installed. Run: pip install gspread google-auth")
        if not credentials_file.exists():
            print(f"    [WARN] No credentials.json found at {credentials_file}")
    
    # Add message handler for custom commands
    def on_message(bot_client, message):
        content = message.content.strip()
        if content.startswith(config.COMMAND_PREFIX):
            if " " in content:
                cmd_part, args = content.split(" ", 1)
            else:
                cmd_part, args = content, ""
            
            cmd = cmd_part[len(config.COMMAND_PREFIX):].lower()
            
            # Check if it's a custom command (not a built-in)
            if not registry.get_command(cmd):
                response = get_custom_command(cmd)
                if response:
                    bot_client.send_message(response)
                    return False  # Stop further processing
        return None
    
    bot.on_message_handlers.append(on_message)
    
    # Load existing commands
    commands = load_custom_commands()
    print(f"    {len(commands)} custom commands loaded")


def teardown(bot):
    """Module teardown"""
    pass
