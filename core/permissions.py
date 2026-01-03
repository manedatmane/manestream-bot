"""
Permission levels and checking for bot commands
"""

from enum import IntEnum
from config import config


class PermissionLevel(IntEnum):
    """Permission levels for commands"""
    EVERYONE = 0      # Anyone can use
    REGISTERED = 1    # Must have account (BongBux)
    TRUSTED = 2       # Trusted users list
    ADMIN = 3         # Admin users only
    OWNER = 4         # Bot owner only


def check_permission(username: str, required_level: PermissionLevel) -> bool:
    """
    Check if user has required permission level
    
    Args:
        username: The username to check
        required_level: The minimum required permission level
        
    Returns:
        True if user has permission, False otherwise
    """
    username_lower = username.lower()
    
    # Owner check (could be expanded to config)
    if required_level == PermissionLevel.OWNER:
        return username_lower == config.ADMIN_USERS[0] if config.ADMIN_USERS else False
    
    # Admin check
    if required_level == PermissionLevel.ADMIN:
        return config.is_admin(username_lower)
    
    # Trusted check (admins are also trusted)
    if required_level == PermissionLevel.TRUSTED:
        return config.is_admin(username_lower)  # Expand this with trusted users list
    
    # Registered check - would need to check if user has account
    if required_level == PermissionLevel.REGISTERED:
        return True  # For now, allow all - modules can check account existence
    
    # Everyone
    return True


def get_user_level(username: str) -> PermissionLevel:
    """
    Get the permission level of a user
    
    Args:
        username: The username to check
        
    Returns:
        The user's permission level
    """
    username_lower = username.lower()
    
    # Check if owner (first admin)
    if config.ADMIN_USERS and username_lower == config.ADMIN_USERS[0]:
        return PermissionLevel.OWNER
    
    # Check if admin
    if config.is_admin(username_lower):
        return PermissionLevel.ADMIN
    
    # Default to everyone
    return PermissionLevel.EVERYONE
