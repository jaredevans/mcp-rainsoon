# Rainsoon MCP

This project provides a simple MCP (Model Context Protocol) server for the Gemini CLI that exposes a single tool: **`check_for_rain`**.
This tool lets you check the near-term probability of rain for a given IP address or your current location.

---

## What is MCP?

**MCP** (Model Context Protocol) is a system that allows the Gemini CLI to securely and reliably interact with local or remote tools.
The `rainsoon_mcp.py` script runs as a local MCP server, making its `check_for_rain` function available as a callable tool inside the Gemini CLI.

---

## Features

### `check_for_rain(ip: str = "", threshold: int = 20) -> dict`

- Checks the probability of rain for a specified IP address.
- If no IP address is provided, it automatically detects your public IP using multiple fallback services.
- You can set a custom **threshold** (in percent) to define what “rain soon” means (default: `20`%).
- Returns a JSON object containing:
  - Location details
  - Rain probability
  - Whether the probability exceeds the threshold
  - A human-readable message

---

## How it Works

The `rainsoon_mcp.py` script is a self-contained MCP server. Its workflow:

1. **IP Address Discovery**
   - If `ip` is provided, uses it.
   - If not, queries a series of external services (`api.ipify.org`, `ipinfo.io/ip`, `icanhazip.com`) to detect your public IP.

2. **Geolocation**
   - Uses the [`geocoder`](https://geocoder.readthedocs.io/) library to get latitude, longitude, and city from the IP address.
   - If geolocation fails for a provided IP, it will attempt to fall back to your detected public IP.

3. **Weather Data**
   - Queries the [Open-Meteo API](https://open-meteo.com/) for hourly precipitation probability for the next 24 hours at the coordinates.

4. **Result**
   - Compares the precipitation probability for the next hour to the threshold.
   - Returns detailed JSON with the location, chance of rain, and a boolean flag.

---

## Configuration

**Install python packages:**

```
pip install "mcp[cli]" requests geocoder
```

Gemini CLI loads MCP server settings from `~/.gemini/settings.json`.

Example configuration:

```
{
  "selectedAuthType": "gemini-api-key",
  "theme": "Default",
  "mcpServers": {
    "rainsoon": {
      "command": "/absolute/path/to/venv/bin/python3",
      "args": ["-u", "/absolute/path/to/rainsoon_mcp.py"],
      "timeout": 15000
    }
  }
}
```

**Fields:**

- **`mcpServers`** — contains all your MCP server configs.
- **`rainsoon`** — the name of this MCP server (used in `/mcp call` commands).
- **`command`** — absolute path to the Python executable inside your virtual environment.
- **`args`**:
  - `-u` → unbuffered output (important for MCP stdio communication).
  - Path to `rainsoon_mcp.py` → must be the absolute path.
- **`timeout`** — time (ms) Gemini CLI will wait for a server response.

⚠ **Important:** Update paths to match your local setup.

---

## How to Use It

Once `settings.json` is set up and Gemini CLI is running:

### **Natural Language**
Gemini CLI can also auto-invoke the tool based on your prompt:
```
Is it going to rain soon?
```

or

```
Will it rain soon for IP 134.231.2.45?
```

Example output in Gemini cli:

```
╭────────────────────────╮
│  > will it rain soon?  │
╰────────────────────────╯

 ╭─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
 │ ✔  check_for_rain (rainsoon MCP Server) {}                                                                                                      │
 │                                                                                                                                                 │
 │    {                                                                                                                                            │
 │      "ip": "96.231.154.148",                                                                                                                    │
 │      "location": "Wheaton",                                                                                                                     │
 │      "lat": 39.0348,                                                                                                                            │
 │      "lng": -77.0533,                                                                                                                           │
 │      "rain": false,                                                                                                                             │
 │      "precipitation_chance": 0,                                                                                                                 │
 │      "threshold": 20,                                                                                                                           │
 │      "message": "No, 0% chance of rain soon in Wheaton.",                                                                                       │
 │      "hour_sample": [                                                                                                                           │
 │        "2025-08-12T00:00",                                                                                                                      │
 │        "2025-08-12T01:00",                                                                                                                      │
 │        "2025-08-12T02:00"                                                                                                                       │
 │      ]                                                                                                                                          │
 │    }                                                                                                                                            │
 ╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
✦ No, 0% chance of rain soon in Wheaton.

```
