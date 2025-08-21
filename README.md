# Rainsoon MCP

This project provides a simple MCP (Model Context Protocol) server for the Gemini CLI that exposes a single tool: **`check_for_rain`** and also a **`/rainsoon`** slash command for quick access.

---

## What is MCP?

**MCP** (Model Context Protocol) allows the Gemini CLI to securely and reliably interact with local or remote tools.  

The `rainsoon_mcp.py` script runs as a local MCP server, making its `check_for_rain` function available as a callable tool inside Gemini CLI.  

With the addition of an **MCP prompt**, Gemini CLI now exposes `/rainsoon` as a native slash command with arguments.

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

## `/rainsoon` Command in Gemini CLI

The MCP server includes a **prompt definition** that Gemini CLI turns into a slash command:

**Usage:**

```
/rainsoon                      # auto-detect IP, default threshold=20%
/rainsoon --ip="134.231.2.45"       # check for a specific IP
/rainsoon --ip="134.231.2.45" --threshold=35
```

The output is the **raw JSON** from `check_for_rain`.

Example:

```
╭───────────────╮
│  > /rainsoon  │
╰───────────────╯

✔  check_for_rain (rainsoon MCP Server) {"threshold":20,"ip":""}

{
  "ip": "96.231.151.145",
  "location": "Wheaton",
  "lat": 39.0358,
  "lng": -77.0523,
  "rain": false,
  "precipitation_chance": 0,
  "threshold": 20,
  "message": "No, 0% chance of rain soon in Wheaton.",
  "hour_sample": [
    "2025-08-12T00:00",
    "2025-08-12T01:00",
    "2025-08-12T02:00"
  ]
}
```

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

## Installation

**Install Python packages:**

```
pip install "mcp[cli]" requests geocoder
```

**Gemini CLI configuration** (`~/.gemini/settings.json`):

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

- `mcpServers` — all MCP server configs.
- `rainsoon` — server name (used in `/mcp call` commands).
- `command` — absolute path to Python in your venv.
- `args` — `-u` for unbuffered output, then absolute path to the script.
- `timeout` — in ms.

⚠ Update the paths for your environment.

---

## How to Use

### Natural Language
Gemini CLI can auto-call the tool when you type:

```
Will it rain soon?
Will it rain soon for IP 134.231.2.45?
Will I be wet soon?
```

### `/rainsoon` Command

```
/rainsoon
/rainsoon --ip="134.231.2.45"
/rainsoon --ip="134.231.2.45" --threshold=35
```

---
