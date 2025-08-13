#!/usr/bin/env python3
"""
rainsoon_mcp.py — Pure MCP server for Gemini CLI (stdio transport).

Tools:
  - check_for_rain(ip: str = "", threshold: int = 20) -> dict
    • If `ip` is provided, uses it.
    • If `ip` is empty, auto-detects the public IP.
    • Returns a compact JSON dict including location, chance, and message.

Prompt (auto slash command in Gemini CLI):
  - /rainsoon [--ip "x.x.x.x"] [--threshold 20]
    • Calls the tool with the given args and returns ONLY the tool's raw JSON.

Deps (install in your venv):
  pip install "mcp[cli]" requests geocoder
"""

from __future__ import annotations

import requests
import geocoder
from mcp.server.fastmcp import FastMCP

# ---------- MCP server ----------
mcp = FastMCP("rainsoon")


def _get_public_ip() -> str:
    """Best-effort public IP discovery with small timeouts."""
    endpoints = [
        "https://api.ipify.org",
        "https://ipinfo.io/ip",
        "https://icanhazip.com",
    ]
    for url in endpoints:
        try:
            ip = requests.get(url, timeout=5).text.strip()
            if ip:
                return ip
        except requests.RequestException:
            pass
    raise RuntimeError("Could not determine public IP from fallback services.")


def _fetch_precip_prob(lat: float, lng: float) -> dict:
    """Fetch the next-hour precipitation probability and times from Open-Meteo."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lng}"
        "&hourly=precipitation_probability"
        "&forecast_days=1"
        "&timezone=auto"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    hourly = data.get("hourly", {})
    probs = hourly.get("precipitation_probability", [])
    times = hourly.get("time", [])
    if not probs:
        raise RuntimeError("Weather data missing precipitation probabilities.")
    return {"prob": int(probs[0]), "times": times[:3] if times else []}


@mcp.tool()
def check_for_rain(ip: str = "", threshold: int = 20) -> dict:
    """
    Check near-term rain probability for an IP address.
    - If `ip` is omitted or blank, auto-detects the current public IP.
    - `threshold` is the percentage considered "rain soon" (default 20).
    """
    # 1) Ensure we have an IP (auto-detect if not provided)
    ip = (ip or "").strip()
    tried_autodetect = False
    try:
        if not ip:
            tried_autodetect = True
            ip = _get_public_ip()
    except Exception as e:
        return {"error": f"Could not determine public IP: {e}"}

    # 2) Geolocate IP (if this fails and we *didn't* autodetect, try autodetect as a fallback)
    def geolocate(target_ip: str):
        g = geocoder.ip(target_ip)
        if not g.ok or not g.latlng:
            raise RuntimeError(f"Could not geolocate IP {target_ip}.")
        lat, lng = g.latlng
        city = g.city or "your area"
        return lat, lng, city

    try:
        lat, lng, city = geolocate(ip)
    except Exception as first_err:
        if not tried_autodetect:
            # Try auto IP as a fallback
            try:
                auto_ip = _get_public_ip()
                lat, lng, city = geolocate(auto_ip)
                ip = auto_ip  # switch to the detected IP
                tried_autodetect = True
            except Exception as second_err:
                return {
                    "error": f"{first_err}; fallback to public IP failed: {second_err}"
                }
        else:
            return {"error": str(first_err)}

    # 3) Weather lookup
    try:
        wx = _fetch_precip_prob(lat, lng)
        p = wx["prob"]
        result = {
            "ip": ip,
            "location": city,
            "lat": lat,
            "lng": lng,
            "rain": bool(p > threshold),
            "precipitation_chance": p,
            "threshold": threshold,
            "message": (
                f"{'Yes' if p > threshold else 'No'}, {p}% chance of rain soon in {city}."
            ),
        }
        if wx["times"]:
            result["hour_sample"] = wx["times"]
        return result
    except requests.RequestException as e:
        return {"error": f"Failed to fetch weather data: {e}"}
    except Exception as e:
        return {"error": str(e)}


# ---------- MCP Prompt -> becomes /rainsoon in Gemini CLI ----------
@mcp.prompt()
def rainsoon(ip: str = "", threshold: int = 20) -> str:
    """
    Prompt that the Gemini CLI exposes as /rainsoon with named args:
      /rainsoon
      /rainsoon --ip "8.8.8.8"
      /rainsoon --ip "8.8.8.8" --threshold 35
    """
    # Keep instructions minimal so the model reliably calls the tool.
    return f"""
Call the tool `check_for_rain` with ip="{ip}" and threshold={int(threshold)}.
Return ONLY the tool's raw JSON (no commentary).
"""


if __name__ == "__main__":
    # Run as an MCP server over stdio (Gemini CLI default)
    mcp.run(transport="stdio")
