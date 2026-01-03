"""
Socket.IO client wrapper for connecting to Manestream Chat
"""

import asyncio
import time
import logging
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass

import socketio

from config import config, DATA_DIR
from .registry import registry, CommandContext


# Configure logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(DATA_DIR / "logs" / "bot.log"),
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class User:
    """Represents a chat user"""
    username: str
    display_name: str
    provider: str
    avatar: str = ""
    is_bot: bool = False
    
    @classmethod
    def from_dict(cls, data: dict) -> "User":
        return cls(
            username=data.get("username", ""),
            display_name=data.get("displayName", data.get("username", "")),
            provider=data.get("provider", "unknown"),
            avatar=data.get("avatar", ""),
            is_bot=data.get("isBot", False),
        )


@dataclass  
class Message:
    """Represents a chat message"""
    id: str
    user: User
    content: str
    timestamp: int
    
    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        return cls(
            id=data.get("id", ""),
            user=User.from_dict(data.get("user", {})),
            content=data.get("content", ""),
            timestamp=data.get("timestamp", 0),
        )


class BotClient:
    """
    Socket.IO client for Manestream Chat bot
    
    Handles connection, reconnection, message processing, and command dispatch.
    """
    
    def __init__(self):
        self.sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite
            reconnection_delay=config.RECONNECT_DELAY,
            reconnection_delay_max=config.MAX_RECONNECT_DELAY,
            logger=logger.level <= logging.DEBUG,
        )
        
        self.connected = False
        self.start_time = time.time()
        self.reconnect_count = 0
        self.messages_processed = 0
        self.commands_processed = 0
        
        # User tracking
        self.online_users: Dict[str, User] = {}
        
        # Event handlers
        self.on_connect_handlers: List[Callable] = []
        self.on_disconnect_handlers: List[Callable] = []
        self.on_message_handlers: List[Callable] = []
        
        # Setup Socket.IO events
        self._setup_events()
    
    def _setup_events(self):
        """Setup Socket.IO event handlers"""
        
        @self.sio.event
        def connect():
            self.connected = True
            logger.info(f"[OK] Connected to {config.CHAT_SERVER_URL}")
            
            for handler in self.on_connect_handlers:
                try:
                    handler(self)
                except Exception as e:
                    logger.error(f"Connect handler error: {e}")
        
        @self.sio.event
        def disconnect():
            self.connected = False
            self.reconnect_count += 1
            logger.warning(f"[DISCONNECTED] from server (reconnect #{self.reconnect_count})")
            
            for handler in self.on_disconnect_handlers:
                try:
                    handler(self)
                except Exception as e:
                    logger.error(f"Disconnect handler error: {e}")
        
        @self.sio.event
        def connect_error(data):
            logger.error(f"Connection error: {data}")
        
        @self.sio.on("message")
        def on_message(data):
            try:
                self._handle_message(data)
            except Exception as e:
                logger.error(f"Message handler error: {e}")
                import traceback
                traceback.print_exc()
        
        @self.sio.on("history")
        def on_history(messages):
            logger.info(f"Received {len(messages)} history messages")
            # Don't process history as commands
        
        @self.sio.on("users")
        def on_users(users):
            self.online_users = {}
            for user_data in users:
                user = User.from_dict(user_data)
                self.online_users[user.username.lower()] = user
            logger.debug(f"{len(self.online_users)} users online")
        
        @self.sio.on("system")
        def on_system(data):
            msg_type = data.get("type", "")
            message = data.get("message", "")
            logger.info(f"System: [{msg_type}] {message}")
        
        @self.sio.on("banned")
        def on_banned(data):
            reason = data.get("reason", "Unknown")
            logger.error(f"Bot was banned: {reason}")
        
        @self.sio.on("error")
        def on_error(data):
            logger.error(f"Server error: {data}")
    
    def _handle_message(self, data: dict):
        """Handle incoming chat message"""
        message = Message.from_dict(data)
        self.messages_processed += 1
        
        # Skip own messages
        if message.user.username.lower() == config.BOT_USERNAME.lower():
            return
        
        # Skip bot messages
        if message.user.is_bot:
            return
        
        logger.debug(f"[MSG] {message.user.display_name}: {message.content}")
        
        # Call message handlers
        for handler in self.on_message_handlers:
            try:
                result = handler(self, message)
                if result is False:
                    return  # Handler wants to stop processing
            except Exception as e:
                logger.error(f"Message handler error: {e}")
        
        # Check for command
        content = message.content.strip()
        if content.startswith(config.COMMAND_PREFIX):
            self._handle_command(message)
    
    def _handle_command(self, message: Message):
        """Handle a command message"""
        content = message.content.strip()
        
        # Parse command and args
        if " " in content:
            cmd_part, args = content.split(" ", 1)
        else:
            cmd_part, args = content, ""
        
        # Remove prefix
        cmd = cmd_part[len(config.COMMAND_PREFIX):].lower()
        
        if not cmd:
            return
        
        # Create context
        ctx = CommandContext(
            bot=self,
            user=message.user,
            message=message.content,
            args=args,
            args_list=args.split() if args else [],
            command=cmd,
        )
        
        # Dispatch to registry
        try:
            # Run synchronously for now
            import asyncio
            loop = asyncio.new_event_loop()
            handled = loop.run_until_complete(registry.handle_command(ctx))
            loop.close()
            
            if handled:
                self.commands_processed += 1
                logger.info(f"Command: !{cmd} by {message.user.display_name}")
                
        except Exception as e:
            logger.error(f"Command dispatch error: {e}")
            import traceback
            traceback.print_exc()
    
    def send_message(self, text: str):
        """
        Send a chat message
        
        Args:
            text: Message text to send
        """
        if not self.connected:
            logger.warning("Cannot send message: not connected")
            return
        
        # Truncate if too long
        if len(text) > config.MAX_MESSAGE_LENGTH:
            text = text[:config.MAX_MESSAGE_LENGTH - 3] + "..."
        
        self.sio.emit("message", text)
        logger.debug(f"Sent: {text[:50]}...")
    
    def connect(self) -> bool:
        """
        Connect to the chat server
        
        Returns:
            True if connected successfully
        """
        logger.info(f"Connecting to {config.CHAT_SERVER_URL}...")
        
        try:
            self.sio.connect(
                config.CHAT_SERVER_URL,
                auth={
                    "username": config.BOT_USERNAME,
                    "displayName": config.BOT_DISPLAY_NAME,
                    "avatar": config.BOT_AVATAR,
                    "isBot": True,
                    "apiKey": config.BOT_API_KEY,
                },
                wait_timeout=10,
            )
            return True
            
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the chat server"""
        if self.connected:
            logger.info("Disconnecting...")
            self.sio.disconnect()
    
    def run(self):
        """
        Run the bot (blocking)
        
        This will connect and maintain connection until interrupted.
        """
        logger.info("=" * 50)
        logger.info(f"{config.BOT_DISPLAY_NAME}")
        logger.info("=" * 50)
        logger.info(f"Server: {config.CHAT_SERVER_URL}")
        logger.info(f"Admins: {', '.join(config.ADMIN_USERS)}")
        logger.info(f"Commands: {len(registry.commands)}")
        logger.info("=" * 50)
        
        while True:
            try:
                if not self.connected:
                    if self.connect():
                        self.sio.wait()
                    else:
                        logger.info(f"Retrying in {config.RECONNECT_DELAY}s...")
                        time.sleep(config.RECONNECT_DELAY)
                else:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                logger.info("\nShutting down...")
                self.disconnect()
                break
                
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(config.RECONNECT_DELAY)
    
    @property
    def uptime(self) -> int:
        """Get bot uptime in seconds"""
        return int(time.time() - self.start_time)
    
    @property
    def stats(self) -> dict:
        """Get bot statistics"""
        return {
            "uptime": self.uptime,
            "connected": self.connected,
            "reconnects": self.reconnect_count,
            "messages_processed": self.messages_processed,
            "commands_processed": self.commands_processed,
            "online_users": len(self.online_users),
        }
