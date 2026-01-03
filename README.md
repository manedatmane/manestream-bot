# Manestream Bot

A modular, production-ready chat bot for the Manestream Chat system. Features fishing, BongBux economy, gambling, custom commands, auto-moderation, and API integrations.

---

## Architecture Overview

```
manestream-bot/
├── bot.py                 # Main bot entry point
├── config.py              # Configuration management
├── core/
│   ├── __init__.py
│   ├── client.py          # Socket.IO client wrapper
│   ├── registry.py        # Command registry system
│   └── permissions.py     # Permission levels
├── modules/
│   ├── __init__.py
│   ├── economy.py         # BongBux system
│   ├── fishing.py         # Fishing game
│   ├── gambling.py        # Slots, roulette, dice
│   ├── custom_commands.py # User-defined commands
│   ├── moderation.py      # Auto-mod, bans
│   ├── api_commands.py    # GIPHY, weather, IMDB
│   ├── utility.py         # !last, !commands, etc.
│   └── fun.py             # Simple responses, arrays
├── data/                  # Persistent data (gitignored)
│   ├── bongbux/
│   ├── fish/
│   ├── custom_commands.json
│   ├── bans.json
│   └── last_seen.json
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd manestream-bot
pip install -r requirements.txt
```

### 2. Configure

Copy the example config and edit:

```bash
cp .env.example .env
```

Edit `.env`:
```env
# Chat server connection
CHAT_SERVER_URL=http://localhost:3000
BOT_API_KEY=your-bot-api-key

# Bot identity
BOT_USERNAME=FishBot
BOT_DISPLAY_NAME=🐟 FishBot
BOT_AVATAR=https://i.imgur.com/yourbot.png

# Admin users (comma-separated)
ADMIN_USERS=bong,saiyajin,north

# Optional API keys
GIPHY_API_KEY=
TENOR_API_KEY=
OMDB_API_KEY=
```

### 3. Run

```bash
# Development
python bot.py

# Production (with auto-restart)
python bot.py --production

# Docker (recommended for 99.9% uptime)
docker-compose up -d
```

---

## Deployment for 99.9% Uptime

### Option A: Docker with Auto-Restart (Recommended)

The included `docker-compose.yml` provides:
- Automatic restart on crash
- Health checks
- Log rotation
- Resource limits

```bash
# Start
docker-compose up -d

# View logs
docker-compose logs -f bot

# Restart
docker-compose restart bot
```

### Option B: Systemd Service

Create `/etc/systemd/system/manestream-bot.service`:

```ini
[Unit]
Description=Manestream Chat Bot
After=network.target

[Service]
Type=simple
User=manestream
WorkingDirectory=/opt/manestream-bot
ExecStart=/usr/bin/python3 bot.py --production
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable manestream-bot
sudo systemctl start manestream-bot
```

### Option C: PM2 (Node.js process manager)

```bash
npm install -g pm2
pm2 start bot.py --interpreter python3 --name manestream-bot
pm2 save
pm2 startup
```

---

## Hosting Recommendations

### Separate from Chat Server (Recommended for Uptime)

Running the bot separately from the chat server provides:
- Independent scaling
- Isolated failures (bot crash doesn't affect chat)
- Easier updates (restart bot without chat downtime)

**Recommended setup:**
- Chat Server: DigitalOcean/Hetzner ($4-6/month)
- Bot: Same server OR separate small VPS ($4/month)

### Same Server (Simpler)

If you run both on the same server:
- Use Docker Compose for both
- Bot failure won't affect chat (separate containers)
- Shared resources may cause issues under load

---

## Modules

### Economy (`modules/economy.py`)

| Command | Description | Example |
|---------|-------------|---------|
| `!bongbux` | Check/create account | `!bongbux` |
| `!give` | Transfer BongBux | `!give @user 100` |
| `!checkbux` | Check another user | `!checkbux @user` |
| `!leaderboard` | Top 5 richest | `!leaderboard` |

**Starting balance:** 100 BongBux

### Fishing (`modules/fishing.py`)

| Command | Description |
|---------|-------------|
| `!fish` | Cast your line |
| `!fishstats` | Your fishing stats |
| `!fishstats @user` | Someone else's stats |
| `!fishleaderboard` | Top fishers |

**Rarities:**
- Common (60%): 4-10 BongBux
- Uncommon (25%): 18-30 BongBux
- Rare (12%): 60-80 BongBux
- Epic (2.5%): 150-200 BongBux
- Legendary (0.5%): 500-1000 BongBux

**Cooldown:** 30 seconds between casts

### Gambling (`modules/gambling.py`)

| Command | Description | Example |
|---------|-------------|---------|
| `!gamble` | 45% chance to 2x | `!gamble 50` |
| `!slots` | Slot machine | `!slots 10` |
| `!roll` | Roll dice (dubs/trips bonus) | `!roll` |
| `!roulette` | Bet on numbers/colors | `!roulette 10 red` |
| `!coinflip` | 50/50 flip | `!coinflip 25 heads` |

### Custom Commands (`modules/custom_commands.py`)

| Command | Description | Permission |
|---------|-------------|------------|
| `!addcmd` | Create command | Anyone |
| `!delcmd` | Delete command | Admin only |
| `!editcmd` | Edit command | Admin only |
| `!cmdinfo` | Show command info | Anyone |

**Example:**
```
!addcmd beer https://i.imgur.com/stonecold.gif
!beer  →  https://i.imgur.com/stonecold.gif
```

### Moderation (`modules/moderation.py`)

| Command | Description | Permission |
|---------|-------------|------------|
| `!ban` | Ban user | Admin |
| `!unban` | Unban user | Admin |
| `!banlist` | Show bans | Admin |
| `!mute` | Mute user | Admin |
| `!unmute` | Unmute user | Admin |

**Auto-moderation:**
- Gibberish username detection (`/^[a-z]{6}\d{4,5}$/`)
- Banned IP range checking
- Configurable via `data/automod_config.json`

### API Commands (`modules/api_commands.py`)

| Command | Description | API Required |
|---------|-------------|--------------|
| `!gif` | Search GIPHY | GIPHY_API_KEY |
| `!pepe` | Random Pepe | TENOR_API_KEY |
| `!wojak` | Random Wojak | TENOR_API_KEY |
| `!imdb` | Movie/TV info | OMDB_API_KEY |
| `!weather` | Weather forecast | None (Open-Meteo) |

### Utility (`modules/utility.py`)

| Command | Description |
|---------|-------------|
| `!last` | When user was last seen |
| `!commands` | List all commands |
| `!help` | Bot help |
| `!ping` | Check bot latency |
| `!uptime` | Bot uptime |
| `!random` | Random command |

### Fun (`modules/fun.py`)

Simple text responses and media arrays:

| Trigger | Response |
|---------|----------|
| `n` | N.jpg |
| `f` | f.jpg |
| `ayy` | lmaoo |
| `based` | based.gif |
| `!mane` | Random mane image |
| `!koth` | Random KOTH clip |

---

## Adding New Modules

1. Create `modules/mymodule.py`:

```python
from core.registry import registry, command

@command("mycommand")
def my_command(ctx, args):
    """My command description"""
    ctx.reply(f"Hello {ctx.user.display_name}!")

@command("adminonly", admin=True)
def admin_command(ctx, args):
    """Admin-only command"""
    ctx.reply("You are an admin!")

def setup(bot):
    """Called when module loads"""
    print("My module loaded!")

def teardown(bot):
    """Called when module unloads"""
    print("My module unloaded!")
```

2. Add to `config.py`:

```python
ENABLED_MODULES = [
    'economy',
    'fishing',
    'mymodule',  # Add here
]
```

3. Restart bot

---

## Data Persistence

All data is stored in the `data/` directory:

| File | Description |
|------|-------------|
| `bongbux/{user}.txt` | User balances |
| `fish/{user}.json` | Fishing stats |
| `custom_commands.json` | User commands |
| `last_seen.json` | Activity tracking |
| `bans.json` | Ban list |

**Backup strategy:**
```bash
# Daily backup cron
0 0 * * * tar -czf /backups/manestream-bot-$(date +\%Y\%m\%d).tar.gz /opt/manestream-bot/data/
```

---

## Configuration Reference

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CHAT_SERVER_URL` | Chat server URL | `http://localhost:3000` |
| `BOT_API_KEY` | Bot authentication key | Required |
| `BOT_USERNAME` | Bot username | `FishBot` |
| `BOT_DISPLAY_NAME` | Display name | `🐟 FishBot` |
| `BOT_AVATAR` | Avatar URL | None |
| `ADMIN_USERS` | Comma-separated admins | `bong,saiyajin,north` |
| `STARTING_BONGBUX` | New account balance | `100` |
| `FISH_COOLDOWN` | Seconds between fish | `30` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

### Runtime Configuration

Edit `data/config.json` for runtime settings:

```json
{
  "fish_cooldown": 30,
  "starting_bongbux": 100,
  "gamble_win_rate": 0.45,
  "max_message_length": 500,
  "automod_enabled": true
}
```

---

## Monitoring & Health

### Health Check Endpoint

The bot exposes a health endpoint (if HTTP server enabled):

```bash
curl http://localhost:3001/health
# {"status": "ok", "uptime": 3600, "connected": true}
```

### Metrics

With `--metrics` flag:
- Commands processed
- Messages seen
- Reconnection count
- Response times

### Logging

Logs go to stdout and `data/logs/bot.log`:

```bash
# View live logs
tail -f data/logs/bot.log

# Docker logs
docker-compose logs -f bot
```

---

## Migration from BOTmk7

Your existing data can be migrated:

```bash
# Copy BongBux data
cp -r /old/bot/bongbux_data/* data/bongbux/

# Copy fish stats
cp -r /old/bot/game_data/fish/* data/fish/

# Copy custom commands
cp /old/bot/custom_commands.json data/

# Copy last seen
cp /old/bot/user_logs/last_seen.json data/
```

---

## Troubleshooting

### Bot won't connect

1. Check chat server is running
2. Verify `BOT_API_KEY` matches server config
3. Check firewall allows connection

### Commands not working

1. Check module is enabled in config
2. Verify command prefix (`!`)
3. Check logs for errors

### Data not saving

1. Ensure `data/` directory is writable
2. Check disk space
3. Verify no file locks

### High memory usage

1. Reduce `MESSAGE_HISTORY_LIMIT`
2. Clean old fish stats
3. Check for memory leaks in custom modules

---

## Contributing

1. Fork the repository
2. Create feature branch
3. Follow existing code style
4. Add tests if applicable
5. Submit pull request

---

## License

MIT License - See LICENSE file
