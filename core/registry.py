"""
Command registry system for modular command handling
"""

import functools
from typing import Callable, Dict, List, Optional, Any
from dataclasses import dataclass, field
from .permissions import PermissionLevel, check_permission


@dataclass
class CommandInfo:
    """Information about a registered command"""
    name: str
    handler: Callable
    description: str = ""
    usage: str = ""
    aliases: List[str] = field(default_factory=list)
    permission: PermissionLevel = PermissionLevel.EVERYONE
    module: str = ""
    hidden: bool = False
    cooldown: int = 0  # Seconds between uses (0 = no cooldown)


@dataclass
class CommandContext:
    """Context passed to command handlers"""
    bot: Any  # BotClient instance
    user: Any  # User object
    message: str  # Full message
    args: str  # Arguments after command
    args_list: List[str]  # Arguments as list
    command: str  # Command that was invoked
    room: str = "public"  # Room the message was sent in
    
    def reply(self, text: str):
        """Send a reply message to the same room"""
        self.bot.send_message(text, room=self.room)
    
    def reply_mention(self, text: str):
        """Send a reply mentioning the user to the same room"""
        self.bot.send_message(f"@{self.user.display_name}: {text}", room=self.room)


class CommandRegistry:
    """Registry for bot commands"""
    
    def __init__(self):
        self.commands: Dict[str, CommandInfo] = {}
        self.aliases: Dict[str, str] = {}  # alias -> command name
        self.cooldowns: Dict[str, Dict[str, float]] = {}  # command -> {user: last_use}
        self.modules: Dict[str, List[str]] = {}  # module -> [command names]
        
        # Hooks for extending functionality
        self.pre_command_hooks: List[Callable] = []
        self.post_command_hooks: List[Callable] = []
    
    def register(
        self,
        name: str,
        handler: Callable,
        description: str = "",
        usage: str = "",
        aliases: List[str] = None,
        permission: PermissionLevel = PermissionLevel.EVERYONE,
        module: str = "",
        hidden: bool = False,
        cooldown: int = 0,
    ) -> CommandInfo:
        """
        Register a command
        
        Args:
            name: Command name (without prefix)
            handler: Function to handle the command
            description: Help text description
            usage: Usage example
            aliases: Alternative names for the command
            permission: Required permission level
            module: Module this command belongs to
            hidden: If True, hide from help listings
            cooldown: Seconds between uses per user
            
        Returns:
            The CommandInfo object
        """
        aliases = aliases or []
        
        cmd_info = CommandInfo(
            name=name.lower(),
            handler=handler,
            description=description,
            usage=usage,
            aliases=[a.lower() for a in aliases],
            permission=permission,
            module=module,
            hidden=hidden,
            cooldown=cooldown,
        )
        
        # Register main command
        self.commands[name.lower()] = cmd_info
        
        # Register aliases
        for alias in aliases:
            self.aliases[alias.lower()] = name.lower()
        
        # Track by module
        if module:
            if module not in self.modules:
                self.modules[module] = []
            self.modules[module].append(name.lower())
        
        return cmd_info
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a command
        
        Args:
            name: Command name to unregister
            
        Returns:
            True if command was removed, False if not found
        """
        name = name.lower()
        
        if name not in self.commands:
            return False
        
        cmd_info = self.commands[name]
        
        # Remove aliases
        for alias in cmd_info.aliases:
            if alias in self.aliases:
                del self.aliases[alias]
        
        # Remove from module tracking
        if cmd_info.module and cmd_info.module in self.modules:
            if name in self.modules[cmd_info.module]:
                self.modules[cmd_info.module].remove(name)
        
        # Remove command
        del self.commands[name]
        
        return True
    
    def get_command(self, name: str) -> Optional[CommandInfo]:
        """
        Get command by name or alias
        
        Args:
            name: Command name or alias
            
        Returns:
            CommandInfo if found, None otherwise
        """
        name = name.lower()
        
        # Check direct match
        if name in self.commands:
            return self.commands[name]
        
        # Check aliases
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        
        return None
    
    def check_cooldown(self, command: str, username: str) -> Optional[int]:
        """
        Check if command is on cooldown for user
        
        Args:
            command: Command name
            username: Username to check
            
        Returns:
            Seconds remaining if on cooldown, None if ready
        """
        import time
        
        cmd_info = self.get_command(command)
        if not cmd_info or cmd_info.cooldown <= 0:
            return None
        
        command = cmd_info.name
        username = username.lower()
        
        if command not in self.cooldowns:
            return None
        
        if username not in self.cooldowns[command]:
            return None
        
        elapsed = time.time() - self.cooldowns[command][username]
        remaining = cmd_info.cooldown - elapsed
        
        if remaining <= 0:
            return None
        
        return int(remaining)
    
    def set_cooldown(self, command: str, username: str):
        """
        Set cooldown for user on command
        
        Args:
            command: Command name
            username: Username
        """
        import time
        
        cmd_info = self.get_command(command)
        if not cmd_info or cmd_info.cooldown <= 0:
            return
        
        command = cmd_info.name
        username = username.lower()
        
        if command not in self.cooldowns:
            self.cooldowns[command] = {}
        
        self.cooldowns[command][username] = time.time()
    
    async def handle_command(self, ctx: CommandContext) -> bool:
        """
        Handle an incoming command
        
        Args:
            ctx: Command context
            
        Returns:
            True if command was handled, False otherwise
        """
        cmd_info = self.get_command(ctx.command)
        
        if not cmd_info:
            return False
        
        # Check permission
        if not check_permission(ctx.user.username, cmd_info.permission):
            ctx.reply("You don't have permission to use this command.")
            return True
        
        # Check cooldown
        remaining = self.check_cooldown(ctx.command, ctx.user.username)
        if remaining:
            ctx.reply(f"Command on cooldown. Wait {remaining}s.")
            return True
        
        # Run pre-command hooks
        for hook in self.pre_command_hooks:
            try:
                result = hook(ctx, cmd_info)
                if result is False:
                    return True  # Hook cancelled command
            except Exception as e:
                print(f"Pre-command hook error: {e}")
        
        # Execute command
        try:
            result = cmd_info.handler(ctx, ctx.args)
            
            # Handle async commands
            if hasattr(result, "__await__"):
                await result
            
            # Set cooldown after successful execution
            self.set_cooldown(ctx.command, ctx.user.username)
            
        except Exception as e:
            print(f"Command error ({cmd_info.name}): {e}")
            import traceback
            traceback.print_exc()
            ctx.reply(f"Error executing command: {e}")
            return True
        
        # Run post-command hooks
        for hook in self.post_command_hooks:
            try:
                hook(ctx, cmd_info)
            except Exception as e:
                print(f"Post-command hook error: {e}")
        
        return True
    
    def list_commands(
        self,
        module: str = None,
        include_hidden: bool = False,
        permission_level: PermissionLevel = PermissionLevel.EVERYONE,
    ) -> List[CommandInfo]:
        """
        List available commands
        
        Args:
            module: Filter by module
            include_hidden: Include hidden commands
            permission_level: Only show commands up to this level
            
        Returns:
            List of CommandInfo objects
        """
        commands = []
        
        for cmd_info in self.commands.values():
            # Filter by module
            if module and cmd_info.module != module:
                continue
            
            # Filter hidden
            if not include_hidden and cmd_info.hidden:
                continue
            
            # Filter by permission
            if cmd_info.permission > permission_level:
                continue
            
            commands.append(cmd_info)
        
        return sorted(commands, key=lambda c: c.name)


# Global registry instance
registry = CommandRegistry()


def command(
    name: str = None,
    description: str = "",
    usage: str = "",
    aliases: List[str] = None,
    admin: bool = False,
    permission: PermissionLevel = None,
    module: str = "",
    hidden: bool = False,
    cooldown: int = 0,
):
    """
    Decorator to register a command
    
    Args:
        name: Command name (defaults to function name)
        description: Help text
        usage: Usage example
        aliases: Alternative names
        admin: Shortcut for admin permission
        permission: Required permission level
        module: Module name
        hidden: Hide from help
        cooldown: Seconds between uses
        
    Example:
        @command("hello", description="Say hello")
        def hello_cmd(ctx, args):
            ctx.reply(f"Hello {ctx.user.display_name}!")
    """
    def decorator(func: Callable) -> Callable:
        cmd_name = name or func.__name__.replace("_cmd", "").replace("cmd_", "")
        
        # Determine permission level
        perm = permission
        if perm is None:
            perm = PermissionLevel.ADMIN if admin else PermissionLevel.EVERYONE
        
        # Get module from function's module name if not specified
        mod = module
        if not mod and hasattr(func, "__module__"):
            mod_name = func.__module__
            if "modules." in mod_name:
                mod = mod_name.split("modules.")[-1]
        
        # Register the command
        registry.register(
            name=cmd_name,
            handler=func,
            description=description or func.__doc__ or "",
            usage=usage,
            aliases=aliases or [],
            permission=perm,
            module=mod,
            hidden=hidden,
            cooldown=cooldown,
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
