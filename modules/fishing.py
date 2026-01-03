"""
Fishing module - Catch fish to earn BongBux

Mechanics (matching BOTmk7):
- Cost: 5 BongBux per cast
- 60% chance of nothing ("Not even a nibble!")
- 40% chance to catch based on individual fish probabilities

Commands:
- !fish - Cast your line (-5 BongBux)
- !fishstats [user] - View fishing statistics
- !fishstats global - View global stats
"""

import json
import random
import time
from pathlib import Path
from typing import Dict, Optional, Any
from dataclasses import dataclass

from core.registry import command, CommandContext
from config import config, DATA_DIR


FISH_DIR = DATA_DIR / "fish"
GLOBAL_STATS_FILE = FISH_DIR / "global_fish_stats.json"

# Rate limiting (5 casts per 5 minutes)
FISHING_LIMIT = 5
WINDOW_SECONDS = 300
fish_cast_times: Dict[str, list] = {}

FISH_COST = 5  # Cost per cast


@dataclass
class Fish:
    """Represents a fish type"""
    name: str
    image: str
    description: str
    prize: int
    probability: float  # As percentage (e.g., 5.00 = 5%)


# Fish definitions from fish_game.csv (excluding "Not even a nibble" which is handled separately)
FISH_TYPES = [
    Fish("Timberland", "https://i.imgur.com/gQFN0Mz.gif", 
         "caught a Timberland! At least it's something", 10, 6.00),
    Fish("Bluegill", "https://i.imgur.com/8Qnf6lo.gif",
         "caught a Bluegill! Bright and scrappy, the Bluegill is a classic, reliable catch", 25, 5.00),
    Fish("Sack of Pondweed", "https://i.imgur.com/IKG0QzR.gif",
         "caught a Sack of Pondweed! Smells like potent gas", 20, 5.00),
    Fish("Smallmouth Bass", "https://i.imgur.com/WIv3gIK.gif",
         "caught a Smallmouth Bass! Smaller, but don't let its size fool you—it puts up a real fight", 75, 4.00),
    Fish("Largemouth Bass", "https://i.imgur.com/nTOUDVO.gif",
         "caught a Largemouth Bass! A classic catch! This one's got a hefty jaw and a mean fight", 100, 4.00),
    Fish("Yellow Perch", "https://i.imgur.com/xli7axF.gif",
         "caught a Yellow Perch! Brightly striped and small, but tasty—perfect for a fish fry", 100, 3.00),
    Fish("Carp", "https://i.imgur.com/faVTTIS.gif",
         "caught a Carp! Large and heavy, this fish can test an angler's patience", 125, 2.50),
    Fish("Frigmouthed Hog-sucker", "https://i.imgur.com/PWBZHl4.gif",
         "caught a Frigmouthed Hogsucker! A slimy, aggressive fish with a lingering bad odor. More trouble than it's worth", -25, 2.50),
    Fish("Sexofish", "https://i.imgur.com/sRUHkg7.gif",
         "caught a Sexofish! A fish that wears a tinfoil hat—no one knows what it's on about", 125, 1.50),
    Fish("Crappie", "https://i.imgur.com/1SRDxlb.gif",
         "caught a Crappie! Not the biggest fish, but plentiful and fun to reel in", 50, 1.50),
    Fish("Eaglefish", "https://i.imgur.com/yGhzrEN.gif",
         "caught an Eaglefish! This fish thinks it's tough but is easily outsmarted", 100, 1.00),
    Fish("Alabama Boigafish", "https://i.imgur.com/1LaMk25.gif",
         "caught an Alabama Boigafish! It looks uncannily like a cheeseburger floating in the water!", 125, 0.80),
    Fish("Alabama Bogfish", "https://i.imgur.com/Hsh32Qu.gif",
         "caught an Alabama Bogfish! This fish loves a good nap but is prone to getting into accidents", 50, 0.80),
    Fish("Northern Pike", "https://i.imgur.com/Jf8ZYqh.gif",
         "caught a Northern Pike! Lean, mean, and toothy. This predator is a fierce challenge", 400, 0.70),
    Fish("Treegerfish", "https://i.imgur.com/sJRTKXN.gif",
         "caught a Treegerfish! Bright pink with a purple star marking, known to hunt dogfish", 400, 0.70),
    Fish("Elongated Beerfish", "https://i.imgur.com/LLYUwPt.gif",
         "caught an Elongated Beerfish! This odd fish propels itself with a jet of frothy, white liquid", 200, 0.70),
    Fish("Northmidwestern Box Carp", "https://i.imgur.com/1UlnMdD.gif",
         "caught a Northmidwestern Box Carp! Resembling cardboard, hard to spot in murky waters", 350, 0.60),
    Fish("Clonkheaded Spiderfish", "https://i.imgur.com/pZJ57sO.gif",
         "caught a Clonkheaded Spiderfish! A fish with an uncanny resemblance to an AK-47. Handle with care", 600, 0.60),
    Fish("Saiyafish", "https://i.imgur.com/qTbwfIT.gif",
         "caught a Saiyafish! A saiyan fish, said to have originated from Houston. Don't make it mad", 500, 0.50),
    Fish("Glowing Fukkkofish", "https://i.imgur.com/ab1VGa3.gif",
         "caught a Glowing Fukkkofish! This fish seems suspiciously interested in your every move. Possibly a government agent", 500, 0.50),
    Fish("Timecarp", "https://i.imgur.com/Z78NNNO.gif",
         "caught a Timecarp! A persistent fish that seems to defy time, flying out of the water to hunt slugs and cats", 200, 0.40),
    Fish("Lake Trout", "https://i.imgur.com/CyR53QL.gif",
         "caught a Lake Trout! Deep, powerful, and a true prize from the depths of cold waters", 500, 0.40),
    Fish("Chipheaded Sherkfish", "https://i.imgur.com/Rkf0vmB.gif",
         "caught a Chipheaded Sherkfish! This hefty fish has a strange microchip attached to it. Who's tracking the Sherk?", 750, 0.40),
    Fish("Rainbow Trout", "https://i.imgur.com/eiotPmb.gif",
         "caught a Rainbow Trout! Famous for its vivid colors, this trout is a sight to behold", 450, 0.40),
    Fish("Haunterfish", "https://i.imgur.com/RBKqmAb.gif",
         "caught a Haunterfish! A terrifying predator that silently stalks Sherkfish and Bogfish. Not for the faint of heart", 800, 0.30),
    Fish("Muskellunge", "https://i.imgur.com/xFlghCH.gif",
         "caught a Muskellunge! The 'fish of 10,000 casts'—a massive, elusive trophy that every angler dreams of catching", 1000, 0.25),
    Fish("Bongofish Rex", "https://i.imgur.com/Z7XLeiV.gif",
         "caught a BONGOFISH REX! The undisputed king of the lake. Sporting a thick moustache, it commands respect from all", 2000, 0.15),
]

# Nothing chance is 60%
NOTHING_CHANCE = 60.0

# Calculate total catch probability (should be ~40%)
TOTAL_CATCH_PROB = sum(f.probability for f in FISH_TYPES)


def get_fish_stats(username: str) -> Dict[str, Any]:
    """Get a user's fishing statistics"""
    filepath = FISH_DIR / f"{username.lower()}_fish.json"
    
    if not filepath.exists():
        return {}
    
    try:
        return json.loads(filepath.read_text())
    except (json.JSONDecodeError, IOError):
        return {}


def save_fish_stats(username: str, stats: Dict[str, Any]):
    """Save a user's fishing statistics"""
    filepath = FISH_DIR / f"{username.lower()}_fish.json"
    filepath.write_text(json.dumps(stats, indent=2))


def get_global_stats() -> Dict[str, int]:
    """Get global fish catch statistics"""
    if not GLOBAL_STATS_FILE.exists():
        return {}
    
    try:
        return json.loads(GLOBAL_STATS_FILE.read_text())
    except:
        return {}


def save_global_stats(stats: Dict[str, int]):
    """Save global statistics"""
    GLOBAL_STATS_FILE.write_text(json.dumps(stats, indent=2))


def add_catch(username: str, fish_name: str):
    """Record a fish catch for user and global stats"""
    # User stats
    stats = get_fish_stats(username)
    stats[fish_name] = stats.get(fish_name, 0) + 1
    save_fish_stats(username, stats)
    
    # Global stats
    global_stats = get_global_stats()
    global_stats[fish_name] = global_stats.get(fish_name, 0) + 1
    save_global_stats(global_stats)


def check_rate_limit(username: str) -> Optional[int]:
    """
    Check if user is rate limited (5 casts per 5 minutes)
    
    Returns:
        Seconds to wait if limited, None if OK
    """
    username = username.lower()
    now = time.time()
    
    if username not in fish_cast_times:
        fish_cast_times[username] = []
    
    # Clean old entries
    fish_cast_times[username] = [
        t for t in fish_cast_times[username]
        if now - t < WINDOW_SECONDS
    ]
    
    if len(fish_cast_times[username]) >= FISHING_LIMIT:
        oldest = min(fish_cast_times[username])
        wait_time = int(WINDOW_SECONDS - (now - oldest))
        return max(1, wait_time)
    
    return None


def record_cast(username: str):
    """Record a fishing cast for rate limiting"""
    username = username.lower()
    if username not in fish_cast_times:
        fish_cast_times[username] = []
    fish_cast_times[username].append(time.time())


def catch_fish() -> Optional[Fish]:
    """
    Attempt to catch a fish based on individual probabilities
    
    Returns:
        Fish if caught, None if nothing
    """
    # Roll 0-100
    roll = random.uniform(0, 100)
    
    # First 60% is nothing
    if roll < NOTHING_CHANCE:
        return None
    
    # Adjust roll to be within the catch range
    # Map the remaining 40% to the fish probabilities
    adjusted_roll = random.uniform(0, TOTAL_CATCH_PROB)
    
    cumulative = 0
    for fish in FISH_TYPES:
        cumulative += fish.probability
        if adjusted_roll < cumulative:
            return fish
    
    # Fallback to last fish (shouldn't happen)
    return FISH_TYPES[-1]


@command(
    "fish",
    description="Cast your line and try to catch a fish! Costs 5 BongBux.",
    usage="!fish",
    aliases=["cast"],
)
def cmd_fish(ctx: CommandContext, args: str):
    """Go fishing! Costs 5 BongBux per cast."""
    from modules.economy import get_balance, set_balance, ensure_account
    
    # Check rate limit
    wait_time = check_rate_limit(ctx.user.username)
    if wait_time:
        minutes = wait_time // 60
        seconds = wait_time % 60
        if minutes > 0:
            ctx.reply(f"You're casting too fast! Wait {minutes}m {seconds}s")
        else:
            ctx.reply(f"You're casting too fast! Wait {seconds}s")
        return
    
    # Ensure account exists and check balance
    balance = ensure_account(ctx.user.username)
    
    if balance < FISH_COST:
        ctx.reply(f"You need at least {FISH_COST} BongBux to fish! You have {balance}.")
        return
    
    # Deduct cost
    balance -= FISH_COST
    set_balance(ctx.user.username, balance)
    
    # Record the cast for rate limiting
    record_cast(ctx.user.username)
    
    # Try to catch
    fish = catch_fish()
    
    if fish is None:
        # Nothing caught
        add_catch(ctx.user.username, "Not even a nibble!")
        ctx.reply(f"Not even a nibble! [-{FISH_COST} BongBux]")
        return
    
    # Caught something!
    add_catch(ctx.user.username, fish.name)
    
    # Award/deduct BongBux based on prize
    new_balance = balance + fish.prize
    if new_balance < 0:
        new_balance = 0
    set_balance(ctx.user.username, new_balance)
    
    # Format prize string
    if fish.prize >= 0:
        prize_str = f"[+{fish.prize} BongBux]"
    else:
        prize_str = f"[{fish.prize} BongBux]"
    
    # Build message - include image
    if fish.prize >= 500:
        # Rare/legendary fish - emphasize it
        ctx.reply(f"*** {ctx.user.display_name} {fish.description} {prize_str} *** {fish.image}")
    elif fish.prize >= 200:
        ctx.reply(f"** {ctx.user.display_name} {fish.description} {prize_str} ** {fish.image}")
    elif fish.prize < 0:
        # Negative fish
        ctx.reply(f"{ctx.user.display_name} {fish.description} {prize_str} {fish.image}")
    else:
        ctx.reply(f"{ctx.user.display_name} {fish.description} {prize_str} {fish.image}")


@command(
    "fishstats",
    description="View fishing statistics",
    usage="!fishstats [username|global]",
    aliases=["fs", "fstats"],
)
def cmd_fishstats(ctx: CommandContext, args: str):
    """View fishing stats for a user or global"""
    arg = args.strip().lower() if args.strip() else ""
    
    if arg == "global":
        # Show global stats
        stats = get_global_stats()
        if not stats:
            ctx.reply("No fish have been caught yet!")
            return
        
        total = sum(stats.values())
        sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]
        top_fish = ", ".join([f"{name}: {count}" for name, count in sorted_stats])
        
        ctx.reply(f"Global Fish Stats ({total} total): {top_fish}")
        return
    
    # User stats
    target = arg.lstrip("@") if arg else ctx.user.username.lower()
    stats = get_fish_stats(target)
    
    if not stats:
        ctx.reply(f"{target} hasn't caught any fish yet!")
        return
    
    total = sum(stats.values())
    nibbles = stats.get("Not even a nibble!", 0)
    catches = total - nibbles
    
    # Top 3 fish (excluding nibbles)
    fish_only = {k: v for k, v in stats.items() if k != "Not even a nibble!"}
    sorted_fish = sorted(fish_only.items(), key=lambda x: x[1], reverse=True)[:3]
    top_fish = ", ".join([f"{name}: {count}" for name, count in sorted_fish])
    
    catch_rate = (catches / total * 100) if total > 0 else 0
    
    ctx.reply(f"{target}'s stats: {catches} fish caught, {nibbles} nibbles ({catch_rate:.0f}% rate) | Top: {top_fish}")


def setup(bot):
    """Module setup"""
    FISH_DIR.mkdir(parents=True, exist_ok=True)
    print(f"    Fish data: {FISH_DIR}")
    print(f"    {len(FISH_TYPES)} fish types loaded")
    print(f"    Rate limit: {FISHING_LIMIT} casts per {WINDOW_SECONDS//60} minutes")


def teardown(bot):
    """Module teardown"""
    pass
