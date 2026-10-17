# Home-Browser MCP

Browse the web through your **home residential IP** — bypass datacenter bans, Cloudflare Turnstile, and anti-bot walls for **Muse, Groq bots, cloud agents, and AI assistants**.

---

## ⚡ One-Click Quickstart (Home Computer)

On the machine at home you want to browse through (Mac, Linux, Raspberry Pi, or Windows):

```bash
git clone https://github.com/onlinegill/home-browser-mcp.git
cd home-browser-mcp
./setup.sh
```

**`./setup.sh` does everything automatically:**
1. ✅ Creates an isolated Python virtual environment.
2. ✅ Installs MCP & Scrapling Stealth dependencies (`patchright`, `curl-cffi`).
3. ✅ Downloads required browser binaries (`scrapling install`).
4. ✅ Detects your Tailscale IP and verifies SSH port 22.
5. ✅ Outputs exact, ready-to-copy configs for **Muse**, **Groq**, **Claude Desktop**, and **Cursor**.

Test it immediately on your home machine:
```bash
./hbm fetch https://example.com
```

---

## The Problem

Anti-bot systems (Cloudflare, Akamai, PerimeterX, Datadome, AWS WAF) use a **two-layer defense**:

```
Layer 1: IP / ASN Reputation      ──▶  Instantly flags Datacenter ASNs (AWS, GCP, VPS, Groq/Muse cloud)
Layer 2: Browser Fingerprinting   ──▶  Instantly flags automation leaks (CDP artifacts, navigator.webdriver)
```

1. **Cloud & VPS IPs are blacklisted by default**: When your Muse or Groq bot fetches an Amazon, retail, or news page from a cloud server, it gets an immediate `403 Forbidden` or Cloudflare challenge because of the datacenter ASN.
2. **Standard headless browsers leak fingerprints**: Even if you route traffic, vanilla headless browsers fail modern JavaScript challenges and Cloudflare Turnstile due to exposed automation flags.

---

## The Solution

Home-Browser MCP pairs a **clean residential ISP connection** with two specialized MCP browser engines:

```
┌─────────────────────────────────────────┐
│  AI Bot or Assistant                    │
│  • Muse bots & Groq agents              │
│  • Claude Code, Cursor, Claude Desktop  │
│  • LangChain / custom cloud agents      │
└────────────────────┬────────────────────┘
                     │ MCP over SSH stdio (Tailscale private network)
                     ▼
┌─────────────────────────────────────────┐
│  Home Computer (Residential IP)         │
│  ┌───────────────────────────────────┐  │
│  │ Engine A: Scrapling MCP (Stealth) │  │ ──▶ Bypasses Cloudflare Turnstile &
│  │           (patchright + curl-cffi)│  │     converts pages to LLM Markdown
│  ├───────────────────────────────────┤  │
│  │ Engine B: Playwright MCP          │  │ ──▶ Interactive clicking, typing,
│  │           (@playwright/mcp)       │  │     and form filling
│  └───────────────────────────────────┘  │
└────────────────────┬────────────────────┘
                     │ Residential ISP IP + Stealth Fingerprint
                     ▼
               🌐 Target Websites
        (No datacenter blocks, no Turnstile walls)
```

### Choose the Engine for Your Task

| Feature | Scrapling Stealth Engine (Default) | Playwright Engine |
| :--- | :---: | :---: |
| **Command** | `scrapling-mcp` | `npx -y @playwright/mcp --headless` |
| **Primary Use Case** | **Groq/Muse bots, scrapers, reading sites** | **Interactive UI automation** |
| **Cloudflare Turnstile Bypass** | **Yes** (via `patchright` & anti-fingerprinting) | Limited (subject to JS challenge) |
| **Output Format** | Clean LLM-ready **Markdown** or JSON | Structured YAML snapshot / element refs |
| **Action Support** | Fetch, bulk fetch, sessions, screenshots | Clicks, typing, key press, snapshots |

---

## Unified CLI (`./hbm`)

The repo provides a single executable tool `./hbm` that auto-detects its environment:

```bash
# Run one-click setup
./hbm setup

# Run self-diagnostics (checks Tailscale, SSH, Scrapling, and live fetch)
./hbm test

# Fetch any website with Cloudflare bypass -> clean LLM Markdown
./hbm fetch https://protected-site.com/products

# Show Tailscale connection info and connection snippets
./hbm info

# Execute multi-step JSON plan from stdin
./hbm drive < plan.json
```

---

## For Muse & Groq Bots (Python SDK)

Import `HomeBrowser` directly into your bot pipeline:

```python
from hbm import HomeBrowser

# Connect to your home PC over Tailscale
hb = HomeBrowser(host="user@100.x.y.z")

# Fetch any site through home residential IP + Scrapling stealth:
# (Automatically bypasses Cloudflare Turnstile and returns clean LLM Markdown)
markdown_content = hb.fetch_markdown("https://target-store.com/deal")
print(markdown_content)
```

### CLI / Shell Integration for Any Cloud Bot
```bash
export HBM_SSH_HOST="user@100.x.y.z"
./hbm fetch https://target-store.com/deal
```

---

## Setup for Native MCP Clients (Claude Desktop, Cursor, Claude Code)

### Claude Desktop
Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "home-stealth-browser": {
      "command": "ssh",
      "args": [
        "user@100.x.y.z",
        "~/.venv/bin/scrapling-mcp"
      ]
    },
    "home-interactive-browser": {
      "command": "ssh",
      "args": [
        "user@100.x.y.z",
        "npx", "-y", "@playwright/mcp", "--headless"
      ]
    }
  }
}
```

### Claude Code
```bash
claude mcp add home-stealth -- ssh user@100.x.y.z scrapling-mcp
```

---

## Troubleshooting & FAQ

- **`ssh` asks for a password**: Configure SSH key authentication (`ssh-copy-id user@home-pc`). MCP clients and bot runners cannot type interactive passwords.
- **Run diagnostics**: Execute `./hbm test` on your home computer to instantly pinpoint whether Tailscale, SSH, or browser binaries need attention.
- **Security**: Traffic travels strictly over encrypted, peer-to-peer Tailscale connections. No open ports on your home router are needed.
