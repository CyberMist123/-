# Signal Bridge Remote Setup — Claude execution guide

> Markdown transcription/normalization of the previously uploaded `Signal Bridge Guide for Claude.pdf`.

## Objective

Expose a local Signal Bridge MCP server over Streamable HTTP through a Cloudflare Tunnel so Claude.ai can reach a Bluetooth accessory through Intiface Central.

Architecture:

```text
Claude.ai
  → Cloudflare Tunnel (HTTPS)
  → Signal Bridge MCP on the user's computer
  → Intiface Central
  → Bluetooth accessory
```

## Prerequisites

Confirm:

1. Windows or macOS/Linux.
2. Python installed.
3. Signal Bridge installed.
4. Intiface Central installed.
5. Compatible Bluetooth accessory available.
6. Claude.ai plan supports custom connectors; otherwise use local Claude Desktop stdio mode.

Install dependencies when needed:

```bash
pip install mcp buttplug python-dotenv
```

## Convert Signal Bridge to Streamable HTTP

The guide proposes changing the MCP construction and run mode:

```python
mcp = FastMCP("Signal Bridge", host="0.0.0.0", port=8888)
...
mcp.run(transport="streamable-http")
```

### Windows encoding warning

Do not use a lossy PowerShell rewrite. Read and write explicitly as UTF-8 without BOM for `.py`:

```powershell
$text = [System.IO.File]::ReadAllText(
  "$pwd\signal_bridge_mcp.py",
  [System.Text.Encoding]::UTF8
)
$text = $text.Replace(
  'FastMCP("Signal Bridge")',
  'FastMCP("Signal Bridge", host="0.0.0.0", port=8888)'
)
$text = $text.Replace(
  'mcp.run()',
  'mcp.run(transport="streamable-http")'
)
[System.IO.File]::WriteAllText(
  "$pwd\signal_bridge_mcp.py",
  $text,
  (New-Object System.Text.UTF8Encoding $false)
)
```

In this Cachito project, the stricter project rule remains:

- `.ps1` UTF-8 with BOM;
- `.py` UTF-8 without BOM;
- `.cmd` ASCII/no BOM and launcher-only.

## Cloudflare Tunnel

Check/install `cloudflared`, then launch with HTTP/2 on Windows:

```powershell
cloudflared tunnel --url http://localhost:8888 --protocol http2
```

The guide warns that default QUIC may be blocked by some Windows networks/proxies.

## Launch order

1. Intiface Central: start server, power on accessory, scan, confirm device.
2. Signal Bridge:

```powershell
python signal_bridge_mcp.py
```

Expected server address:

```text
http://0.0.0.0:8888
```

3. Cloudflare Tunnel:

```powershell
cloudflared tunnel --url http://localhost:8888 --protocol http2
```

4. Add the custom connector in Claude.ai using:

```text
https://<tunnel-host>/mcp
```

5. Open a new conversation and verify `list_devices`.

## Troubleshooting captured in the guide

| Symptom | Likely cause | Fix |
|---|---|---|
| Python reports non-UTF-8 source | unsafe PowerShell rewrite | restore/rewrite with explicit UTF-8 encoding |
| QUIC dial failure | QUIC blocked | use `--protocol http2` |
| unexpected `host` argument in `run()` | MCP SDK API mismatch | put host/port in `FastMCP(...)`; keep transport in `run()` |
| Claude Desktop local config stops working | server changed from stdio to HTTP | keep separate local and remote entry points |
| Claude.ai connector fails later | tunnel stopped or URL changed | restart tunnel/update connector |

## Security notes

- A random temporary tunnel URL is not a substitute for authentication.
- Close the tunnel and server when not in use.
- Prefer a bearer token or another explicit access control for persistent deployment.
- Do not expose control tools without an emergency stop and bounded parameters.

## Relevance to Cachito

This guide is downstream infrastructure, not a transport solution. It becomes useful only after Cachito is controllable through one of:

- official remote-session emulation;
- direct GATT;
- a phone/board BLE advertisement bridge;
- Intiface support.

It should not drive protocol decisions, but it provides a reusable path from a verified local controller to Claude.ai.
