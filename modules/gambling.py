"""
Gambling module - Various games of chance (matching BOTmk7)

Commands:
- !slots - Slot machine (-5 to play, special jackpots)
- !roll - Roll dice (free, dubs/trips/quads prizes)
- !d20 - Roll a D20 (-5 to play, nat20 wins, nat1 loses)
- !roulette <amount> on <bet> - Roulette betting
- !coinflip <amount> <heads/tails> - 50/50 coin flip
- !gamble <amount> - Simple 45% chance to double
"""

import random
from typing import Optional, Tuple

from core.registry import command, CommandContext
from config import config


def parse_bet_amount(args: str, balance: int) -> Tuple[Optional[int], Optional[str]]:
    """
    Parse bet amount from args
    
    Args:
        args: The arguments string
        balance: User's current balance
        
    Returns:
        Tuple of (amount, error_message) - amount is None if error
    """
    if not args.strip():
        return None, "Please specify an amount!"
    
    amount_str = args.split()[0].lower()
    
    if amount_str in ("all", "max", "yolo"):
        return balance, None
    
    if amount_str == "half":
        return balance // 2, None
    
    try:
        amount = int(amount_str)
    except ValueError:
        return None, "Amount must be a number!"
    
    if amount <= 0:
        return None, "Amount must be positive!"
    
    if amount > balance:
        return None, f"You only have {balance:,} BongBux!"
    
    return amount, None


@command(
    "slots",
    description="Play the slot machine! Costs 5 BongBux.",
    usage="!slots",
    aliases=["slot"],
)
def cmd_slots(ctx: CommandContext, args: str):
    """
    Slot machine matching BOTmk7
    Special jackpots: 777, Weed, Mane, Ramen
    """
    from modules.economy import get_balance, set_balance, ensure_account
    
    SLOTS_COST = 5
    
    balance = ensure_account(ctx.user.username)
    
    if balance < SLOTS_COST:
        ctx.reply(f"You need {SLOTS_COST} BongBux to play slots!")
        return
    
    # Deduct cost
    balance -= SLOTS_COST
    
    # Slot symbols with weights
    symbols = [
        ("7", 5),
        ("Weed", 8),
        ("Mane", 10),
        ("Ramen", 10),
        ("Cherry", 20),
        ("Lemon", 20),
        ("Orange", 15),
        ("Grape", 12),
    ]
    
    # Flatten for weighted choice
    symbol_list = []
    for sym, weight in symbols:
        symbol_list.extend([sym] * weight)
    
    # Roll three reels
    reels = [random.choice(symbol_list) for _ in range(3)]
    
    # Calculate winnings
    payout = 0
    jackpot_name = ""
    
    if reels[0] == reels[1] == reels[2]:
        # Three of a kind!
        if reels[0] == "7":
            payout = 6969
            jackpot_name = "JACKPOT 777"
        elif reels[0] == "Weed":
            payout = 420
            jackpot_name = "WEED BONUS"
        elif reels[0] == "Mane":
            payout = 500
            jackpot_name = "MANE BONUS"
        elif reels[0] == "Ramen":
            payout = 350
            jackpot_name = "RAMEN BONUS"
        elif reels[0] == "Cherry":
            payout = 100
        elif reels[0] == "Lemon":
            payout = 75
        elif reels[0] == "Orange":
            payout = 80
        elif reels[0] == "Grape":
            payout = 90
    elif reels[0] == reels[1] or reels[1] == reels[2] or reels[0] == reels[2]:
        # Two of a kind
        payout = 15
    elif "Cherry" in reels:
        # Cherry pays something
        payout = 5
    
    result_display = f"[{reels[0]}] [{reels[1]}] [{reels[2]}]"
    
    if payout > 0:
        net = payout - SLOTS_COST
        new_balance = balance + payout
        set_balance(ctx.user.username, new_balance)
        
        if jackpot_name:
            ctx.reply(f"{result_display} *** {jackpot_name}! *** {ctx.user.display_name} wins {payout} BongBux!")
        else:
            ctx.reply(f"{result_display} {ctx.user.display_name} wins {payout} BongBux!")
    else:
        set_balance(ctx.user.username, balance)
        ctx.reply(f"{result_display} No win. [-{SLOTS_COST} BongBux]")


@command(
    "roll",
    description="Roll dice - dubs/trips/quads win prizes! (Free)",
    usage="!roll",
    aliases=["dice"],
)
def cmd_roll(ctx: CommandContext, args: str):
    """Roll dice with special number bonuses - FREE to play"""
    from modules.economy import get_balance, set_balance, ensure_account
    
    # Roll a number 0-999999
    roll = random.randint(0, 999999)
    roll_str = f"{roll:06d}"
    
    # Check for special patterns
    prize = 0
    prize_name = ""
    
    # Check from right to left for repeating digits
    if roll_str[5] == roll_str[4] == roll_str[3] == roll_str[2] == roll_str[1] == roll_str[0]:
        prize = 50000
        prize_name = "SEXTS"
    elif roll_str[5] == roll_str[4] == roll_str[3] == roll_str[2] == roll_str[1]:
        prize = 10000
        prize_name = "QUINTS"
    elif roll_str[5] == roll_str[4] == roll_str[3] == roll_str[2]:
        prize = 1000
        prize_name = "QUADS"
    elif roll_str[5] == roll_str[4] == roll_str[3]:
        prize = 100
        prize_name = "TRIPS"
    elif roll_str[5] == roll_str[4]:
        prize = 25
        prize_name = "DUBS"
    
    # Special number bonuses
    if roll_str == "696969":
        prize = 6969
        prize_name = "NICE"
    elif roll_str == "420420":
        prize = 4200
        prize_name = "BLAZE IT"
    elif roll_str == "000000":
        prize = 10000
        prize_name = "ABSOLUTE ZERO"
    
    msg = f"{ctx.user.display_name} rolled {roll_str}"
    
    if prize > 0:
        ensure_account(ctx.user.username)
        balance = get_balance(ctx.user.username)
        set_balance(ctx.user.username, balance + prize)
        msg += f" - {prize_name}! +{prize} BongBux!"
    
    ctx.reply(msg)


@command(
    "d20",
    description="Roll a D20! Costs 5 BongBux. Nat20=+20, Nat1=-10",
    usage="!d20",
)
def cmd_d20(ctx: CommandContext, args: str):
    """Roll a D20 - costs 5, nat20 wins 20, nat1 loses 10"""
    from modules.economy import get_balance, set_balance, ensure_account
    
    D20_COST = 5
    
    balance = ensure_account(ctx.user.username)
    
    if balance < D20_COST:
        ctx.reply(f"You need {D20_COST} BongBux to roll!")
        return
    
    # Deduct cost
    balance -= D20_COST
    
    # Roll the d20
    roll = random.randint(1, 20)
    
    if roll == 20:
        # Natural 20!
        prize = 20
        new_balance = balance + prize
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"{ctx.user.display_name} rolled a NAT 20! [+{prize} BongBux]")
    elif roll == 1:
        # Natural 1 - critical fail
        penalty = 10
        new_balance = balance - penalty
        if new_balance < 0:
            new_balance = 0
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"{ctx.user.display_name} rolled a NAT 1! Critical fail! [-{penalty + D20_COST} BongBux]")
    else:
        # Normal roll - just lose the cost
        set_balance(ctx.user.username, balance)
        ctx.reply(f"{ctx.user.display_name} rolled a {roll}. [-{D20_COST} BongBux]")


@command(
    "coinflip",
    description="Flip a coin - 50/50 odds",
    usage="!coinflip <amount> <heads/tails>",
    aliases=["cf", "flip"],
)
def cmd_coinflip(ctx: CommandContext, args: str):
    """Coin flip - pick heads or tails"""
    from modules.economy import get_balance, set_balance, ensure_account
    
    parts = args.split()
    
    if len(parts) < 2:
        ctx.reply("Usage: !coinflip <amount> <heads/tails>")
        return
    
    balance = ensure_account(ctx.user.username)
    amount, error = parse_bet_amount(parts[0], balance)
    
    if error:
        ctx.reply(error)
        return
    
    if amount == 0:
        ctx.reply("You need BongBux to flip!")
        return
    
    choice = parts[1].lower()
    if choice not in ("heads", "tails", "h", "t"):
        ctx.reply("Pick heads or tails!")
        return
    
    choice = "heads" if choice in ("heads", "h") else "tails"
    
    # Flip the coin
    result = random.choice(["heads", "tails"])
    
    if choice == result:
        winnings = amount * 2
        new_balance = balance + amount
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"It's {result}! {ctx.user.display_name} won {winnings:,} BongBux!")
    else:
        new_balance = balance - amount
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"It's {result}! {ctx.user.display_name} lost {amount:,} BongBux")


@command(
    "roulette",
    description="Bet on roulette numbers or colors",
    usage="!roulette <amount> on <bet>",
    aliases=["rl"],
)
def cmd_roulette(ctx: CommandContext, args: str):
    """
    Roulette betting - matching BOTmk7
    
    Bets:
    - Number (0-36): 35x payout
    - red/black: 2x payout
    - odd/even: 2x payout
    - low (1-18) / high (19-36): 2x payout
    """
    from modules.economy import get_balance, set_balance, ensure_account
    
    # Parse "amount on bet" format
    if " on " not in args.lower():
        ctx.reply("Usage: !roulette <amount> on <number|red|black|odd|even|low|high>")
        return
    
    parts = args.lower().split(" on ")
    if len(parts) != 2:
        ctx.reply("Usage: !roulette <amount> on <bet>")
        return
    
    balance = ensure_account(ctx.user.username)
    amount, error = parse_bet_amount(parts[0].strip(), balance)
    
    if error:
        ctx.reply(error)
        return
    
    if amount == 0:
        ctx.reply("You need BongBux to play roulette!")
        return
    
    bet = parts[1].strip()
    
    # Red numbers on a roulette wheel
    red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
    
    # Spin the wheel
    result = random.randint(0, 36)
    is_red = result in red_numbers
    is_black = result != 0 and not is_red
    
    color = "Red" if is_red else ("Green" if result == 0 else "Black")
    
    # Check bet
    win = False
    multiplier = 0
    
    try:
        number = int(bet)
        if 0 <= number <= 36:
            win = (result == number)
            multiplier = 35
    except ValueError:
        if bet == "red":
            win = is_red
            multiplier = 2
        elif bet == "black":
            win = is_black
            multiplier = 2
        elif bet == "odd":
            win = result % 2 == 1 and result != 0
            multiplier = 2
        elif bet == "even":
            win = result % 2 == 0 and result != 0
            multiplier = 2
        elif bet == "low":
            win = 1 <= result <= 18
            multiplier = 2
        elif bet == "high":
            win = 19 <= result <= 36
            multiplier = 2
        else:
            ctx.reply("Invalid bet! Use: number (0-36), red, black, odd, even, low, high")
            return
    
    result_text = f"{color} {result}"
    
    if win:
        winnings = amount * multiplier
        net = winnings - amount
        new_balance = balance + net
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"[{result_text}] {ctx.user.display_name} wins {winnings:,} BongBux! (x{multiplier})")
    else:
        new_balance = balance - amount
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"[{result_text}] {ctx.user.display_name} loses {amount:,} BongBux")


@command(
    "gamble",
    description="45% chance to double your bet",
    usage="!gamble <amount>",
    aliases=["bet"],
)
def cmd_gamble(ctx: CommandContext, args: str):
    """Simple gambling - 45% chance to win 2x"""
    from modules.economy import get_balance, set_balance, ensure_account
    
    balance = ensure_account(ctx.user.username)
    amount, error = parse_bet_amount(args, balance)
    
    if error:
        ctx.reply(error)
        return
    
    if amount == 0:
        ctx.reply("You need BongBux to gamble!")
        return
    
    # 45% chance to win
    if random.random() < 0.45:
        winnings = amount * 2
        new_balance = balance + amount
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"{ctx.user.display_name} WON {winnings:,} BongBux! Balance: {new_balance:,}")
    else:
        new_balance = balance - amount
        set_balance(ctx.user.username, new_balance)
        ctx.reply(f"{ctx.user.display_name} lost {amount:,} BongBux... Balance: {new_balance:,}")


def setup(bot):
    """Module setup"""
    print(f"    Games: slots, roll, d20, roulette, coinflip, gamble")


def teardown(bot):
    """Module teardown"""
    pass
