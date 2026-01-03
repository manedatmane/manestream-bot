"""
API commands module - External API integrations

Commands:
- !gif <search> - Search GIPHY
- !pepe - Random Pepe (Tenor)
- !wojak - Random Wojak (Tenor)
- !imdb <title> - Movie/TV info
- !weather <city> - Weather forecast
"""

import random
from typing import Optional
import urllib.parse

from core.registry import command, CommandContext
from config import config


# Try to import requests, but make it optional
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def make_request(url: str, params: dict = None, headers: dict = None) -> Optional[dict]:
    """Make HTTP GET request and return JSON"""
    if not HAS_REQUESTS:
        return None
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"API request error: {e}")
    
    return None


@command(
    "gif",
    description="Search for a GIF on GIPHY",
    usage="!gif <search term>",
    aliases=["giphy"],
)
def cmd_gif(ctx: CommandContext, args: str):
    """Search GIPHY for a GIF"""
    if not config.GIPHY_API_KEY:
        ctx.reply("GIPHY API key not configured")
        return
    
    if not args.strip():
        ctx.reply("Usage: !gif <search term>")
        return
    
    data = make_request(
        "https://api.giphy.com/v1/gifs/search",
        params={
            "api_key": config.GIPHY_API_KEY,
            "q": args.strip(),
            "limit": 10,
            "rating": "r",
        }
    )
    
    if not data or not data.get("data"):
        ctx.reply("No GIFs found!")
        return
    
    # Pick a random result
    gif = random.choice(data["data"])
    url = gif.get("images", {}).get("original", {}).get("url", "")
    
    if url:
        ctx.reply(url)
    else:
        ctx.reply("Couldn't get GIF URL")


@command(
    "tenor",
    description="Search for a GIF on Tenor",
    usage="!tenor <search term>",
)
def cmd_tenor(ctx: CommandContext, args: str):
    """Search Tenor for a GIF"""
    if not config.TENOR_API_KEY:
        ctx.reply("Tenor API key not configured")
        return
    
    if not args.strip():
        ctx.reply("Usage: !tenor <search term>")
        return
    
    data = make_request(
        "https://tenor.googleapis.com/v2/search",
        params={
            "key": config.TENOR_API_KEY,
            "q": args.strip(),
            "limit": 10,
        }
    )
    
    if not data or not data.get("results"):
        ctx.reply("No GIFs found!")
        return
    
    # Pick a random result
    gif = random.choice(data["results"])
    url = gif.get("media_formats", {}).get("gif", {}).get("url", "")
    
    if url:
        ctx.reply(url)
    else:
        ctx.reply("Couldn't get GIF URL")


@command(
    "pepe",
    description="Random Pepe GIF",
    usage="!pepe",
)
def cmd_pepe(ctx: CommandContext, args: str):
    """Get a random Pepe GIF from Tenor"""
    if not config.TENOR_API_KEY:
        ctx.reply("Tenor API key not configured")
        return
    
    data = make_request(
        "https://tenor.googleapis.com/v2/search",
        params={
            "key": config.TENOR_API_KEY,
            "q": "pepe the frog",
            "limit": 20,
        }
    )
    
    if not data or not data.get("results"):
        ctx.reply("No Pepes found!")
        return
    
    gif = random.choice(data["results"])
    url = gif.get("media_formats", {}).get("gif", {}).get("url", "")
    
    if url:
        ctx.reply(url)
    else:
        ctx.reply("Couldn't get Pepe")


@command(
    "wojak",
    description="Random Wojak GIF",
    usage="!wojak",
)
def cmd_wojak(ctx: CommandContext, args: str):
    """Get a random Wojak GIF from Tenor"""
    if not config.TENOR_API_KEY:
        ctx.reply("Tenor API key not configured")
        return
    
    data = make_request(
        "https://tenor.googleapis.com/v2/search",
        params={
            "key": config.TENOR_API_KEY,
            "q": "wojak",
            "limit": 20,
        }
    )
    
    if not data or not data.get("results"):
        ctx.reply("No Wojaks found!")
        return
    
    gif = random.choice(data["results"])
    url = gif.get("media_formats", {}).get("gif", {}).get("url", "")
    
    if url:
        ctx.reply(url)
    else:
        ctx.reply("Couldn't get Wojak")


@command(
    "imdb",
    description="Get movie/TV info from OMDB",
    usage="!imdb <title> [-tv/-m]",
    aliases=["movie", "film"],
)
def cmd_imdb(ctx: CommandContext, args: str):
    """Look up movie/TV info"""
    if not config.OMDB_API_KEY:
        ctx.reply("OMDB API key not configured")
        return
    
    if not args.strip():
        ctx.reply("Usage: !imdb <title>")
        return
    
    # Check for type flags
    title = args.strip()
    media_type = None
    
    if title.endswith(" -tv"):
        title = title[:-4].strip()
        media_type = "series"
    elif title.endswith(" -m"):
        title = title[:-3].strip()
        media_type = "movie"
    
    params = {
        "apikey": config.OMDB_API_KEY,
        "t": title,
        "plot": "short",
    }
    
    if media_type:
        params["type"] = media_type
    
    data = make_request("https://www.omdbapi.com/", params=params)
    
    if not data or data.get("Response") == "False":
        ctx.reply(f"Couldn't find: {title}")
        return
    
    # Format response
    title = data.get("Title", "Unknown")
    year = data.get("Year", "?")
    rating = data.get("imdbRating", "N/A")
    genre = data.get("Genre", "Unknown")
    plot = data.get("Plot", "")
    
    # Truncate plot if too long
    if len(plot) > 150:
        plot = plot[:147] + "..."
    
    ctx.reply(f"🎬 {title} ({year}) - ⭐ {rating} | {genre} | {plot}")


@command(
    "weather",
    description="Get weather forecast",
    usage="!weather <city>",
    aliases=["wx"],
)
def cmd_weather(ctx: CommandContext, args: str):
    """Get weather for a city using Open-Meteo (no API key needed)"""
    if not args.strip():
        ctx.reply("Usage: !weather <city>")
        return
    
    city = args.strip()
    
    # First, geocode the city
    geo_data = make_request(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1}
    )
    
    if not geo_data or not geo_data.get("results"):
        ctx.reply(f"Couldn't find city: {city}")
        return
    
    location = geo_data["results"][0]
    lat = location["latitude"]
    lon = location["longitude"]
    name = location.get("name", city)
    country = location.get("country", "")
    
    # Get weather
    weather_data = make_request(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "temperature_unit": "fahrenheit",
        }
    )
    
    if not weather_data or not weather_data.get("current_weather"):
        ctx.reply("Couldn't get weather data")
        return
    
    current = weather_data["current_weather"]
    temp = current.get("temperature", "?")
    wind = current.get("windspeed", "?")
    
    # Weather code to description
    weather_codes = {
        0: "☀️ Clear",
        1: "🌤️ Mainly clear",
        2: "⛅ Partly cloudy",
        3: "☁️ Overcast",
        45: "🌫️ Foggy",
        48: "🌫️ Rime fog",
        51: "🌧️ Light drizzle",
        53: "🌧️ Drizzle",
        55: "🌧️ Heavy drizzle",
        61: "🌧️ Light rain",
        63: "🌧️ Rain",
        65: "🌧️ Heavy rain",
        71: "🌨️ Light snow",
        73: "🌨️ Snow",
        75: "🌨️ Heavy snow",
        77: "🌨️ Snow grains",
        80: "🌧️ Light showers",
        81: "🌧️ Showers",
        82: "🌧️ Heavy showers",
        85: "🌨️ Light snow showers",
        86: "🌨️ Snow showers",
        95: "⛈️ Thunderstorm",
        96: "⛈️ Thunderstorm with hail",
        99: "⛈️ Severe thunderstorm",
    }
    
    code = current.get("weathercode", 0)
    condition = weather_codes.get(code, "Unknown")
    
    ctx.reply(f"🌡️ {name}, {country}: {temp}°F, {condition}, Wind: {wind} mph")


def setup(bot):
    """Module setup"""
    apis_configured = []
    
    if config.GIPHY_API_KEY:
        apis_configured.append("GIPHY")
    if config.TENOR_API_KEY:
        apis_configured.append("Tenor")
    if config.OMDB_API_KEY:
        apis_configured.append("OMDB")
    
    apis_configured.append("Open-Meteo (no key)")
    
    print(f"    🌐 APIs: {', '.join(apis_configured)}")


def teardown(bot):
    """Module teardown"""
    pass
