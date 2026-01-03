"""
Economy module - BongBux currency system

Commands:
- !bongbux - Check/create your balance
- !give <user> <amount> - Transfer BongBux
- !checkbux <user> - Check someone's balance
- !leaderboard - Top 5 richest users
"""

from pathlib import Path
from typing import Optional

from core.registry import command, CommandContext
from core.permissions import PermissionLevel
from config import config, DATA_DIR


BONGBUX_DIR = DATA_DIR / "bongbux"


def get_balance(username: str) -> Optional[int]:
    """
    Get a user's BongBux balance
    
    Args:
        username: The username to check
        
    Returns:
        Balance if account exists, None otherwise
    """
    filepath = BONGBUX_DIR / f"{username.lower()}.txt"
    
    if not filepath.exists():
        return None
    
    try:
        return int(filepath.read_text().strip())
    except (ValueError, IOError):
        return None


def set_balance(username: str, amount: int):
    """
    Set a user's BongBux balance
    
    Args:
        username: The username
        amount: New balance amount
    """
    filepath = BONGBUX_DIR / f"{username.lower()}.txt"
    filepath.write_text(str(int(amount)))


def add_balance(username: str, amount: int) -> int:
    """
    Add to a user's balance (can be negative)
    
    Args:
        username: The username
        amount: Amount to add (negative to subtract)
        
    Returns:
        New balance
    """
    current = get_balance(username) or 0
    new_balance = current + amount
    set_balance(username, new_balance)
    return new_balance


def ensure_account(username: str) -> int:
    """
    Ensure user has an account, create if needed
    
    Args:
        username: The username
        
    Returns:
        Current balance
    """
    balance = get_balance(username)
    
    if balance is None:
        set_balance(username, config.STARTING_BONGBUX)
        return config.STARTING_BONGBUX
    
    return balance


@command(
    "bongbux",
    description="Check your BongBux balance (creates account if needed)",
    usage="!bongbux",
    aliases=["balance", "bal", "bb"],
)
def cmd_bongbux(ctx: CommandContext, args: str):
    """Check or create BongBux account"""
    balance = get_balance(ctx.user.username)
    
    if balance is None:
        # Create account
        set_balance(ctx.user.username, config.STARTING_BONGBUX)
        ctx.reply(f"💰 Welcome! You've been given {config.STARTING_BONGBUX} BongBux to start!")
    else:
        ctx.reply(f"💰 {ctx.user.display_name} has {balance:,} BongBux")


@command(
    "give",
    description="Give BongBux to another user",
    usage="!give <username> <amount>",
    aliases=["transfer", "pay"],
)
def cmd_give(ctx: CommandContext, args: str):
    """Transfer BongBux to another user"""
    parts = args.split()
    
    if len(parts) < 2:
        ctx.reply("Usage: !give <username> <amount>")
        return
    
    target = parts[0].lstrip("@").lower()
    
    try:
        amount = int(parts[1])
    except ValueError:
        ctx.reply("Amount must be a number!")
        return
    
    if amount <= 0:
        ctx.reply("Amount must be positive!")
        return
    
    # Check sender balance
    sender_balance = get_balance(ctx.user.username)
    
    if sender_balance is None:
        ctx.reply("You don't have an account! Use !bongbux first.")
        return
    
    if amount > sender_balance:
        ctx.reply(f"You only have {sender_balance:,} BongBux!")
        return
    
    # Check target has account
    target_balance = get_balance(target)
    
    if target_balance is None:
        ctx.reply(f"{target} doesn't have an account yet!")
        return
    
    # Prevent self-transfer
    if target == ctx.user.username.lower():
        ctx.reply("You can't give BongBux to yourself!")
        return
    
    # Do transfer
    set_balance(ctx.user.username, sender_balance - amount)
    set_balance(target, target_balance + amount)
    
    ctx.reply(f"💸 {ctx.user.display_name} gave {amount:,} BongBux to {target}")


@command(
    "checkbux",
    description="Check another user's balance",
    usage="!checkbux <username>",
    aliases=["checkbal", "cb"],
)
def cmd_checkbux(ctx: CommandContext, args: str):
    """Check someone else's BongBux balance"""
    if not args.strip():
        ctx.reply("Usage: !checkbux <username>")
        return
    
    target = args.split()[0].lstrip("@").lower()
    balance = get_balance(target)
    
    if balance is None:
        ctx.reply(f"{target} doesn't have an account yet!")
    else:
        ctx.reply(f"💰 {target} has {balance:,} BongBux")


@command(
    "leaderboard",
    description="Show the top 5 richest users",
    usage="!leaderboard",
    aliases=["lb", "top", "rich"],
)
def cmd_leaderboard(ctx: CommandContext, args: str):
    """Show BongBux leaderboard"""
    # Get all balances
    balances = []
    
    for filepath in BONGBUX_DIR.glob("*.txt"):
        username = filepath.stem
        balance = get_balance(username)
        if balance is not None:
            balances.append((username, balance))
    
    if not balances:
        ctx.reply("No one has BongBux yet!")
        return
    
    # Sort by balance
    balances.sort(key=lambda x: x[1], reverse=True)
    
    # Show top 5
    top = balances[:5]
    lb_text = " | ".join([f"{i+1}. {u}: {b:,}" for i, (u, b) in enumerate(top)])
    
    ctx.reply(f"🏆 Richest: {lb_text}")


@command(
    "setbux",
    description="Set a user's balance (admin only)",
    usage="!setbux <username> <amount>",
    admin=True,
    hidden=True,
)
def cmd_setbux(ctx: CommandContext, args: str):
    """Admin command to set balance"""
    parts = args.split()
    
    if len(parts) < 2:
        ctx.reply("Usage: !setbux <username> <amount>")
        return
    
    target = parts[0].lstrip("@").lower()
    
    try:
        amount = int(parts[1])
    except ValueError:
        ctx.reply("Amount must be a number!")
        return
    
    set_balance(target, amount)
    ctx.reply(f"✅ Set {target}'s balance to {amount:,} BongBux")


def setup(bot):
    """Module setup"""
    # Ensure directory exists
    BONGBUX_DIR.mkdir(parents=True, exist_ok=True)
    print(f"    📁 BongBux data: {BONGBUX_DIR}")


def teardown(bot):
    """Module teardown"""
    pass
