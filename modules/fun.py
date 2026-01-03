"""
Fun module - Array commands and simple responses (matching BOTmk7)

Array Commands:
- !koth - Random King of the Hill clip
- !tc - Random TC post
- !mcs - Magic Conch Shell
- !tits - NSFW
- !ass - NSFW
- !tna - NSFW (both)
- !ted - Random Ted post
- !mane - Random Mane post
- !north - Random North gif

Simple Triggers:
- n -> N.jpg
- f -> f.jpg
- ayy -> lmaoo
- based -> based.gif
- etc.
"""

import random
from typing import Optional

from core.registry import command, CommandContext
from config import config


# ============================================================================
# ARRAYS FROM array_commands.py
# ============================================================================

KOTH_LINKS = [
    'https://i.ibb.co/894QtQ9/koth30.gif', 'https://i.ibb.co/Jd6WdBJ/koth29.gif',
    'https://i.ibb.co/7zRm407/koth28.gif', 'https://i.ibb.co/LvLCdRB/koth27.gif',
    'https://i.ibb.co/1Yc0mbF/koth26.gif', 'https://i.ibb.co/bNYJFc0/koth25.gif',
    'https://i.ibb.co/Vvf5YxQ/koth24.gif', 'https://i.ibb.co/jhcLLNY/koth23.gif',
    'https://i.ibb.co/GCt7qXf/koth22.gif', 'https://i.ibb.co/0tX8xcP/koth21.gif',
    'https://i.ibb.co/R6KY99T/koth20.gif', 'https://i.ibb.co/sK95qWD/koth19.gif',
    'https://i.ibb.co/9cCm15M/koth18.gif', 'https://i.ibb.co/gFhJL2H/koth17.gif',
    'https://i.ibb.co/gyv7zFN/koth16.gif', 'https://i.ibb.co/5kBTNBM/koth15.gif',
    'https://i.ibb.co/ZHQTGP0/koth14.gif', 'https://i.ibb.co/VmVCqQ6/koth13.gif',
    'https://i.ibb.co/Q8jhjJp/koth12.gif', 'https://i.ibb.co/p2xkPX3/koth11.gif',
    'https://i.ibb.co/RThSbbX/koth10.gif', 'https://i.ibb.co/ZTt4FJg/koth09.gif',
    'https://i.ibb.co/W6NqGdK/koth08.gif', 'https://i.ibb.co/qd2NcBx/koth07.gif',
    'https://i.ibb.co/6sPZsyD/koth06.gif', 'https://i.ibb.co/hmFNF47/koth05.gif',
    'https://i.ibb.co/QjHBMDx/koth04.gif', 'https://i.ibb.co/ZVgrTRG/koth03.gif',
    'https://i.ibb.co/8jxwwjs/koth02.gif', 'https://i.ibb.co/qyM5Rx7/koth01.gif',
    'https://i.ibb.co/JR6FCtSD/tc-deserve.jpg'
]

TC_POSTS = [
    'WAIT WHAT IS GOING ON HERE', 
    'https://i.ibb.co/JR6FCtSD/tc-deserve.jpg', 
    'HOLD ON TELL ME FROM THE START PLZ',
    'VROOM VROOM',
    'STOP YOU MUST TELL ME FROM THE BEGINNING WHAT HAPPENED',
    'austrian autist',
    'rain man lol',
    'Im gonna slaughter Ankh',
    'Kurt, ive had a long day of being a big shot pilot please inform me of your suffering',
    '!ankh',
    'https://i.ibb.co/27wWkrns/tc-koth.png',
    'https://i.ibb.co/qF3LC2j5/will-tc.jpg',
    'https://i.ibb.co/C5SPQjBC/tc-beastiality.png',
    'https://i.ibb.co/Cvy9K9G/tc-bux-begger.jpg', 
    'https://i.ibb.co/N6MrSW8V/tc-abuse.jpg',
    'https://i.ibb.co/HLgVVQrt/bong-tc.jpg'
]

MAGIC_CONCH = [
    'Maybe someday.',
    'what?',
    'I dont think so.',
    'No.',
    'Yes.',
    'It is certain.',
    'Nigga why you askin me?',
    'You buggin',
    'Hell yeah.',
    'Idk you do you nigga',
    'Yeah just do it stop askin'
]

TIT_LINKS = [
    'https://i.ibb.co/cgbB6cZ/Uniform-Glaring-Dromaeosaur-size-restricted.gif', 
    'https://i.ibb.co/Q9zdBxZ/371846.gif', 'https://i.ibb.co/0FyvVPd/Shimmering-Needy-Emu-size-restricted.gif',
    'https://i.ibb.co/YQNV8WR/beautiful-cocksucker-gets-every-last-drop.gif', 'https://i.ibb.co/CWwCdB9/3777.gif', 'https://i.ibb.co/W6yTYtw/034-1000.gif',
    'https://i.ibb.co/vzYVKpx/036-1000.gif', 'https://i.ibb.co/6RKhJ6V/023-1000.gif', 'https://i.ibb.co/s2YTyfW/020-1000.gif', 'https://i.ibb.co/tc4RtjT/005-1000.gif',
    'https://i.ibb.co/kGFWKP4/994-1000.gif', 'https://i.ibb.co/Rc9YYz4/julebrus-ik4ks-c60803.gif', 'https://i.ibb.co/PQZYbh7/rFlGZ3c.gif', 'https://i.ibb.co/S0HThfK/titty-drop-reveal.gif',
    'https://i.ibb.co/ZWZ591P/hotboobsdropreveal-15823135158c4pl.gif', 'https://i.ibb.co/QQWJtSt/733-1000.gif', 'https://i.ibb.co/0DMKLxR/realnakedgirls-0025.gif',
    'https://i.ibb.co/ZH2vcX7/035-1000.gif', 'https://i.ibb.co/ZG1cvwc/536-1000.gif', 'https://i.ibb.co/MPFVGGk/exploited66-ksi8x-7cd93c.gif', 'https://i.ibb.co/0jGWQY6/333.gif',
    'https://i.ibb.co/hddkMpz/EmaYmZQ.gif', 'https://i.ibb.co/qNYw9s4/respectable-boob-drop.gif', 'https://i.ibb.co/s2YTyfW/020-1000.gif', 'https://i.ibb.co/C6CfmW2/Damp-Red-Iberianmidwifetoad-size-restricted.gif',
    'https://i.ibb.co/sCX82Bz/556-450.gif', 'https://i.ibb.co/PYph5DD/anylovefortanlines-1578155852c48pl.gif', 'https://i.ibb.co/WGHCXTf/Flamboyant-Euphoric-Galapagosdove-size-restricted.gif',
    'https://i.ibb.co/MC76vDN/tumblr-p9h21h-MJGX1xv0plqo1-400.gif', 'https://i.ibb.co/kDLqPND/4DBD106.gif', 'https://i.ibb.co/fqP7btB/727-1000.gif', 'https://i.ibb.co/4Rzz8pM/unnamed.gif',
    'https://i.ibb.co/NCZ6yrK/kwje3jI.gif', 'https://i.ibb.co/5LDp3vT/vhujrn19zva21.gif', 'https://i.ibb.co/VHzMqxS/uioum6oh33uz.gif', 'https://i.ibb.co/NtWDDj2/tumblr-pdlyf8063b1xc5zrlo1-400.gif',
    'https://i.ibb.co/kmW934s/tits33.gif', 'https://i.ibb.co/mcpYrLj/tits32.gif', 'https://i.ibb.co/7bV3b3s/tits31.gif', 'https://i.ibb.co/Khbxv9q/tits30.gif', 'https://i.ibb.co/V9XrP6c/tits29.gif',
    'https://i.ibb.co/bJkT8JG/tits28.gif', 'https://i.ibb.co/VVzZgBZ/tits27.gif', 'https://i.ibb.co/qxpBY9n/tits26.gif', 'https://i.ibb.co/JrG999P/tits25.gif', 'https://i.ibb.co/MC8wJSZ/tits24.gif',
    'https://i.ibb.co/Yb7rKf3/tits23.gif', 'https://i.ibb.co/zN20PXk/tits22.gif', 'https://i.ibb.co/b1gfh9S/tits21.gif', 'https://i.ibb.co/LQrJ5vQ/tits20.gif', 'https://i.ibb.co/q09J78d/tits19.gif',
    'https://i.ibb.co/C0bZXkS/tits18.gif', 'https://i.ibb.co/T13frKW/tits17.gif', 'https://i.ibb.co/ZV39Ms6/tits16.gif', 'https://i.ibb.co/QDXcgnN/tits15.gif', 'https://i.ibb.co/R6YNXVh/tits14.gif',
    'https://i.ibb.co/w6DN7L6/tits13.gif', 'https://i.ibb.co/rHk40Nj/tits12.gif', 'https://i.ibb.co/9sSQCy1/tits11.gif', 'https://i.ibb.co/4fjGc2G/tits10.gif', 'https://i.ibb.co/kXQrTJD/tits09.gif',
    'https://i.ibb.co/Kh9zMnT/tits08.gif', 'https://i.ibb.co/vw0BQf4/tits07.gif', 'https://i.ibb.co/6ZXLyvh/tits06.gif', 'https://i.ibb.co/8XPT25B/tits05.gif', 'https://i.ibb.co/gDm1q7n/tits04.gif',
    'https://i.ibb.co/Yc9QRBw/tits02.gif', 'https://i.ibb.co/J7ZfDdc/tits01.gif'
]

ASS_LINKS = [
    'https://i.ibb.co/Z8R7vjs/ass-22.gif', 
    'https://i.ibb.co/gZY0MpQ/ass-21.gif', 'https://i.ibb.co/JpM87xy/ass-20.gif', 'https://i.ibb.co/899kbvL/ass-19.gif', 'https://i.ibb.co/Y27g07c/ass-18.gif',
    'https://i.ibb.co/KN18nFk/ass-17.gif', 'https://i.ibb.co/kHKCNMy/ass-16.gif', 'https://i.ibb.co/XkBJfrQ/ass-15.gif', 'https://i.ibb.co/jGsQGCt/ass-14.gif', 'https://i.ibb.co/sPzh7cm/ass-13.gif',
    'https://i.ibb.co/3FMGhGX/ass-12.gif', 'https://i.ibb.co/swFj3f5/ass-11.gif', 'https://i.ibb.co/CHj6Zbd/ass-10.gif', 'https://i.ibb.co/KFncDtD/ass-9.gif', 'https://i.ibb.co/SXg7cd8/ass-8.gif',
    'https://i.ibb.co/10zj1DJ/ass-7.gif', 'https://i.ibb.co/hsBdsfM/ass-6.gif', 'https://i.ibb.co/8XsMSJj/ass-5.gif', 'https://i.ibb.co/cFqG1cW/ass-4.gif', 'https://i.ibb.co/Zc8NFny/ass-3.gif',
    'https://i.ibb.co/JdQ7Wcj/ass-2.gif', 'https://i.ibb.co/6mwdRRG/ass-1.gif', 'https://i.ibb.co/mtLddrj/butt29.gif', 'https://i.ibb.co/VxNxwjL/butt28.gif', 'https://i.ibb.co/k5YPfzG/butt27.gif',
    'https://i.ibb.co/qDkWtW4/butt26.gif', 'https://i.ibb.co/Bs757XK/butt25.gif', 'https://i.ibb.co/374wH2L/butt24.gif', 'https://i.ibb.co/grDQYsW/butt23.gif', 'https://i.ibb.co/khfXYPh/butt22.gif',
    'https://i.ibb.co/wc0b6zV/butt21.gif', 'https://i.ibb.co/FD1jXjr/butt20.gif', 'https://i.ibb.co/MPb9XpF/butt18.gif', 'https://i.ibb.co/6mMynL0/butt17.gif', 'https://i.ibb.co/6wsFF5g/butt15.gif',
    'https://i.ibb.co/C9B4nLp/butt14.gif', 'https://i.ibb.co/514JVKr/butt13.gif', 'https://i.ibb.co/yRZcm4T/butt12.gif', 'https://i.ibb.co/hDQ8wNv/butt11.gif', 'https://i.ibb.co/19YcYDn/butt10.gif',
    'https://i.ibb.co/pvNvqvS/butt09.gif', 'https://i.ibb.co/6Xc8jf9/butt08.gif', 'https://i.ibb.co/vXr0mvj/butt07.gif', 'https://i.ibb.co/dmDsCpV/butt06.gif', 'https://i.ibb.co/m9Nq0Mn/butt05.gif',
    'https://i.ibb.co/WHM4TNc/butt04.gif', 'https://i.ibb.co/sjYyZNc/butt03.gif', 'https://i.ibb.co/YtTSHBR/butt02.gif', 'https://i.ibb.co/7tZ96bh/butt01.gif'
]

TED_POSTS = [
    'https://i.ibb.co/92Q5qXL/ted07.jpg', 
    'https://i.ibb.co/cLd2N6k/ted06.jpg', 'https://i.ibb.co/jbqvp7N/ted05.jpg',
    'https://i.ibb.co/2WzXRLn/ted04.jpg', 'https://i.ibb.co/jhGVSng/ted03.jpg', 'https://i.ibb.co/bg475gK/ted02.jpg',
    'https://i.ibb.co/VYg11Kk/ted01.jpg',
    'While I nodded, nearly napping, suddenly there came a clapping. As of ass cheeks gently clapping, clapping at my chamber door. "Tis a visitor, I muttered, dummy thicc and nothing more."'
]

MANE_POSTS = [
    'Das it', 
    'https://bongstream.live/wp-content/uploads/2020/06/sosa.gif',
    '!fwm', '!deadniggas', '!spooky', '!beer', '!pour', '!thisnigga', '!pstriple', '!dd', '!dmx', '!kneel', '!manekwon'
]

NORTH_LINKS = [
    'https://i.ibb.co/gLgz9SM9/18.gif', 'https://i.ibb.co/spDKNWBj/17.gif',
    'https://i.ibb.co/JWKydWNX/16.gif', 'https://i.ibb.co/27HcQ0hj/15.gif',
    'https://i.ibb.co/b5MY3YyL/14.gif', 'https://i.ibb.co/4gCdm568/13.gif',
    'https://i.ibb.co/Q7zy3gnW/12.gif', 'https://i.ibb.co/FkHd3hBG/11.gif',
    'https://i.ibb.co/5gDXMDn1/10.gif', 'https://i.ibb.co/hJj7n3WJ/9.gif',
    'https://i.ibb.co/b5xgbXdM/8.gif', 'https://i.ibb.co/ksF1nzDF/7.gif',
    'https://i.ibb.co/MkkZGVhh/6.gif', 'https://i.ibb.co/p6hdtycX/5.gif',
    'https://i.ibb.co/ymcGdth0/4.gif', 'https://i.ibb.co/B5kRTLdD/3.gif',
    'https://i.ibb.co/Qv84kSzM/2.gif', 'https://i.ibb.co/1JLbv8ys/1.gif',
    'https://i.ibb.co/yBMH412y/20.gif', 'https://i.ibb.co/wFNh3PVp/image.gif'
]


# ============================================================================
# SIMPLE RESPONSES (from BOTmk7.py onMessage)
# ============================================================================

SIMPLE_RESPONSES = {
    "n": "https://i.ibb.co/Sw6vL0Y4/N.jpg",
    "f": "https://i.ibb.co/kVQ8Nvmd/f.jpg",
    "based": "https://i.ibb.co/kM4WZFT/based.gif",
    "banned": "https://i.ibb.co/tTMPK4M5/ump.gif",
    "what?": "https://i.ibb.co/ds4jbvfP/what.gif",
}

PREFIX_RESPONSES = {
    "ayy": "lmaoo",
    "wooo": "https://i.ibb.co/4rvBDK9/woo.gif",
}

PHRASE_RESPONSES = {
    ("anons", "hang"): "https://i.ibb.co/nsx5hyN9/noose-png-35248.png",
}


# ============================================================================
# ARRAY COMMANDS
# ============================================================================

@command("koth", description="Random King of the Hill clip")
def cmd_koth(ctx: CommandContext, args: str):
    ctx.reply(random.choice(KOTH_LINKS))


@command("tc", description="Random TC post")
def cmd_tc(ctx: CommandContext, args: str):
    ctx.reply(random.choice(TC_POSTS))


@command("mcs", description="Ask the Magic Conch Shell", aliases=["conch", "8ball"])
def cmd_mcs(ctx: CommandContext, args: str):
    ctx.reply(random.choice(MAGIC_CONCH))


@command("tits", description="Random tits gif (NSFW)")
def cmd_tits(ctx: CommandContext, args: str):
    ctx.reply(random.choice(TIT_LINKS))


@command("ass", description="Random ass gif (NSFW)")
def cmd_ass(ctx: CommandContext, args: str):
    ctx.reply(random.choice(ASS_LINKS))


@command("tna", description="Random tits and ass (NSFW)")
def cmd_tna(ctx: CommandContext, args: str):
    ctx.reply(random.choice(ASS_LINKS) + " " + random.choice(TIT_LINKS))


@command("ted", description="Random Ted post")
def cmd_ted(ctx: CommandContext, args: str):
    ctx.reply(random.choice(TED_POSTS))


@command("mane", description="Random Mane post")
def cmd_mane(ctx: CommandContext, args: str):
    ctx.reply(random.choice(MANE_POSTS))


@command("north", description="Random North gif")
def cmd_north(ctx: CommandContext, args: str):
    ctx.reply(random.choice(NORTH_LINKS))


# ============================================================================
# UTILITY COMMANDS
# ============================================================================

@command("choose", description="Choose between options", usage="!choose option1 or option2", aliases=["pick"])
def cmd_choose(ctx: CommandContext, args: str):
    if not args.strip():
        ctx.reply("Usage: !choose option1 or option2 or option3")
        return
    
    if " or " in args.lower():
        options = [o.strip() for o in args.split(" or ")]
    elif "," in args:
        options = [o.strip() for o in args.split(",")]
    else:
        options = args.split()
    
    options = [o for o in options if o]
    
    if len(options) < 2:
        ctx.reply("Give me at least 2 options!")
        return
    
    ctx.reply(f"I choose: {random.choice(options)}")


@command("rate", description="Rate something out of 10", usage="!rate <thing>")
def cmd_rate(ctx: CommandContext, args: str):
    if not args.strip():
        ctx.reply("Usage: !rate <thing>")
        return
    
    rating = random.randint(0, 10)
    ctx.reply(f"I rate {args.strip()} a {rating}/10")


# ============================================================================
# SIMPLE RESPONSE HANDLER
# ============================================================================

def check_simple_response(message: str) -> Optional[str]:
    """Check if message matches a simple response trigger"""
    words = message.lower().split()
    if not words:
        return None
    
    first_word = words[0]
    
    # Check exact match triggers (first word only)
    if first_word in SIMPLE_RESPONSES:
        return SIMPLE_RESPONSES[first_word]
    
    # Check prefix triggers
    msg_lower = message.lower()
    for prefix, response in PREFIX_RESPONSES.items():
        if msg_lower.startswith(prefix):
            return response
    
    # Check phrase triggers
    word_set = set(words)
    for phrase_words, response in PHRASE_RESPONSES.items():
        if all(word in word_set for word in phrase_words):
            return response
    
    return None


def setup(bot):
    """Module setup - add simple response handler"""
    
    def simple_response_handler(bot_client, message):
        """Handle simple word/phrase triggers"""
        content = message.content.strip()
        
        # Don't respond to commands
        if content.startswith(config.COMMAND_PREFIX):
            return None
        
        response = check_simple_response(content)
        if response:
            bot_client.send_message(response)
            return False  # Stop processing
        
        # Special case: "i miss ted"
        if "i miss ted" in content.lower():
            import time
            bot_client.send_message("THE")
            time.sleep(0.5)
            bot_client.send_message("BONGO")
            time.sleep(0.5)
            bot_client.send_message("KING")
            return False
        
        return None
    
    bot.on_message_handlers.append(simple_response_handler)
    print(f"    Array commands: koth, tc, mcs, tits, ass, tna, ted, mane, north")
    print(f"    Simple triggers: {len(SIMPLE_RESPONSES) + len(PREFIX_RESPONSES)} loaded")


def teardown(bot):
    """Module teardown"""
    pass
