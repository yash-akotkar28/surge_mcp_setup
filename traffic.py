import os, httpx, asyncio
from mcp.server.fastmcp import FastMCP   # high-level builder

API_KEY = os.getenv("TOMTOM_API_KEY")    # <–– add to .env or Claude config
BASE_TMPL = (
    "https://api.tomtom.com/traffic/services/4/"
    "flowSegmentData/{style}/{length_km}/json"
)

mcp = FastMCP("traffic")                 # name Claude displays

def _status_from_jam(jam_factor: float) -> str:
    """Heuristic status label from TomTom jamFactor (0-10)."""
    if jam_factor < 4:
        return "free"
    if jam_factor < 8:
        return "moderate"
    return "heavy"

@mcp.tool()
async def traffic_flow(
    lat: float,
    lon: float,
    length_km: int = 10,
    style: str = "absolute",
    units: str = "KMPH",
) -> dict:
    """
    Live traffic flow for the road segment closest to (*lat*,*lon*).

    Args
    ----
    lat, lon      : coordinates in EPSG-4326
    length_km     : segment length (1-100 km, TomTom default 5)
    style         : 'absolute' | 'relative' | 'relative-delay'
    units         : 'KMPH' | 'MPH'
    """
    url = BASE_TMPL.format(style=style, length_km=length_km)
    params = {"point": f"{lat},{lon}", "key": API_KEY, "unit": units}

    # TLS verification OFF ── remove verify=False for production
    async with httpx.AsyncClient(timeout=8, verify=False) as client:
        r = await client.get(url, params=params)
        r.raise_for_status()
    seg = r.json()["flowSegmentData"]           # :contentReference[oaicite:0]{index=0}

    jam = seg.get("jamFactor", 0)
    return {
        "coordinates": {"lat": lat, "lon": lon},
        "segment_length_km": length_km,
        "current_speed": seg["currentSpeed"],
        "free_flow_speed": seg["freeFlowSpeed"],
        "current_travel_time_s": seg["currentTravelTime"],
        "free_flow_travel_time_s": seg["freeFlowTravelTime"],
        "confidence": seg["confidence"],
        "jam_factor": jam,
        "traffic_status": _status_from_jam(jam),  # free / moderate / heavy
        "road_closure": seg.get("roadClosure", False),
        "frc": seg["frc"],                       # functional road class
    }

if __name__ == "__main__":
    # stdio transport → ready for Claude Desktop
    mcp.run(transport="stdio")