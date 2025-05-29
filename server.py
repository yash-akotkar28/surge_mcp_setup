# src/surge_mcp/server.py
import os, httpx, asyncio
from mcp.server.fastmcp import FastMCP     # new high-level builder

API_KEY  = os.getenv("OPENWEATHER_API_KEY")
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

mcp = FastMCP("weather")                   # name visible to Claude/Desktop

@mcp.tool()
async def current_weather(city: str, units: str = "metric") -> dict:
    """Return live weather for *city* from OpenWeather."""
    params = {"q": city, "appid": API_KEY, "units": units}
    async with httpx.AsyncClient(timeout=8, verify=False) as client:
        r = await client.get(BASE_URL, params=params)
        r.raise_for_status()
    data  = r.json()
    main  = data["main"]
    w     = data["weather"][0]
    wind  = data["wind"]
    return {
        "location":   data["name"],
        "temperature": main["temp"],
        "feels_like": main["feels_like"],
        "conditions": w["description"],
        "humidity":   main["humidity"],
        "wind_kts":   wind["speed"],
        "icon":       w["icon"],
    }

if __name__ == "__main__":
    # stdio transport → perfect for Claude Desktop
    mcp.run(transport="stdio")
