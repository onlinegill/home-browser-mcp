# Home-Browser MCP

Browse the web through your **home residential IP** — bypass datacenter bans, Cloudflare Turnstile, and anti-bot walls for **Muse, Groq bots, cloud agents, and AI assistants**.

---

## ⚡ One-Click Quickstart (Home Computer)

On the machine at home you want to browse through:

#### 🍏 macOS / 🐧 Linux / 🥧 Raspberry Pi:
```bash
git clone https://github.com/onlinegill/home-browser-mcp.git
cd home-browser-mcp
./setup.sh
```

#### 🪟 Windows (Command Prompt or PowerShell):
```cmd
git clone https://github.com/onlinegill/home-browser-mcp.git
cd home-browser-mcp
setup.bat
```
*(Or in PowerShell: `.\setup.ps1`)*

**The setup script does everything automatically:**
1. ✅ **Detects OS & Python**: Configures environment across macOS, Linux (Debian, Ubuntu, Proxmox, Arch), and Raspberry Pi.
2. ✅ **Auto-installs System Packages**: Automatically detects and installs missing `python3-venv` / `pip` on Debian/Ubuntu/Proxmox systems.
3. ✅ **Tailscale Network Check**: Checks for Tailscale; if missing, optionally offers one-click install so remote bots can connect without router port-forwarding.
4. ✅ **Virtual Environment & Dependencies**: Initializes isolated `.venv` and installs MCP + Scrapling stealth engines (`patchright`, `curl-cffi`, `mcp`).
5. ✅ **Stealth Browser Binaries**: Downloads required stealth browser drivers (`scrapling install`).
6. ✅ **Global CLI Shortcut**: Symlinks `hbm` to your PATH (`/usr/local/bin/hbm` or `~/.local/bin/hbm`).
7. ✅ **Instant Integration Configs**: Automatically outputs personalized, copy-pasteable JSON configs and prompts for **Muse**, **Groq**, **Claude Desktop**, and **Cursor**.

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

# Log into Amazon or other accounts once with 2FA to save persistent session
./hbm login amazon.com

# Show copy-pasteable MCP & AI bot configs (Claude, Cursor, Muse, Groq)
./hbm config

# Show raw network and Tailscale status
./hbm info

# Execute multi-step JSON plan from stdin
./hbm drive < plan.json
```

---

## 🔐 Logging Into Amazon & Accounts (Session Persistence)

To let Muse or your AI assistant access your logged-in Amazon account (cart, orders, Prime prices, search) without asking Muse to handle passwords or 2FA:

1. **On your home Mac/PC, run:**
   ```bash
   ./hbm login amazon.com
   ```
2. A visible browser window will open on your Mac with the persistent profile directory `~/.home-browser-profile`.
3. Sign into your Amazon account, approve your 2FA / SMS prompt, check **"Keep me signed in"**, and simply **close the browser window**.
4. That's it! Your session cookies and storage tokens remain saved locally in `~/.home-browser-profile`.
5. Whenever Muse, Claude, or Groq runs an interactive browser session, **Home-Browser MCP automatically loads this profile**. Amazon will recognize your logged-in session immediately.


---

## 🤖 Connecting & Using With Muse Agent (Step-by-Step)

### Step 1: Get Your Personalized Connection Info
Run `./hbm config` on your home computer or server. It automatically detects your Tailscale IP, username, and binary paths:
```bash
./hbm config
```

---

### Step 2: How to Ask Muse to Add the Connection

Depending on how you interact with Muse, use one of the following methods:

#### Method A: By Prompting Muse Agent in Chat
Send this exact prompt to your Muse agent:

> *"I want you to connect to my home browser MCP server so you can browse the web through my home residential IP and bypass anti-bot blocks. Please connect to the MCP server named `home-browser` using this command:*
> 
> `ssh user@<tailscale-ip> /path/to/home-browser-mcp/.venv/bin/scrapling-mcp`
> 
> *Once connected, confirm which tools are available."*

*(Replace `user@<tailscale-ip>` and the path with the values printed by `./hbm config`)*.

#### Method B: In Muse / Client MCP Settings (`mcp.json`)
If your Muse client or assistant has an MCP configuration file:

```json
{
  "mcpServers": {
    "home-browser": {
      "command": "ssh",
      "args": [
        "user@<tailscale-ip>",
        "/path/to/home-browser-mcp/.venv/bin/scrapling-mcp"
      ]
    }
  }
}
```

*(If Muse runs on the exact same machine as Home-Browser MCP, omit `"command": "ssh"` and simply put `"command": "/path/to/home-browser-mcp/.venv/bin/scrapling-mcp"`)*.

---

### Step 3: Example Prompts to Ask Muse Agent

Once connected, ask Muse to browse, search, or scrape naturally:

#### 🛍️ 1. Search Amazon & Compare Products
> *"Use the `home-browser` tool to open amazon.com and search for 'wireless noise cancelling headphones'. Give me a comparison of the top 3 results including price, Prime shipping availability, and customer rating."*

#### 🛡️ 2. Read Cloudflare / Protected Sites
> *"Fetch the article at `https://protected-site.com/deep-dive` using `home-browser`. It has Cloudflare Turnstile protection, so make sure to fetch it through my home browser tool and summarize the key takeaways in bullet points."*

#### 🛒 3. Check Logged-in Cart or Orders (Amazon / Retail)
> *(Make sure you ran `./hbm login amazon.com` once beforehand on your home machine)*  
> *"Use `home-browser` to check my Amazon cart at https://www.amazon.com/gp/cart/view.html and list the items and total estimated cost."*

#### 📉 4. Stock & Price Monitoring
> *"Check https://www.amazon.com/dp/B08N5WRWNW using `home-browser`. Tell me if it is currently in stock, who the seller is, and what the current price is."*

---

## 🐍 For Muse & Groq Bots (Python SDK)

If you are building custom Muse bot workflows, Groq pipelines, or LangChain agents in Python:

```python
from hbm import HomeBrowser

# Connect to your home PC over Tailscale (or omit host if running locally):
hb = HomeBrowser(host="user@100.x.y.z")

# Fetch any site through home residential IP + Scrapling stealth:
# (Automatically bypasses Cloudflare Turnstile and returns clean LLM Markdown)
markdown_content = hb.fetch_markdown("https://amazon.com/s?k=mechanical+keyboard")
print(markdown_content)
```

### CLI / Shell Integration for Any Cloud Bot
```bash
export HBM_SSH_HOST="user@100.x.y.z"
./hbm fetch amazon.com
```

---

## 💻 Setup for Other MCP Clients (Cursor, Claude Desktop, Windsurf, Cline)

Run `./hbm config` to see your exact paths pre-filled, or use the templates below:

### Cursor (`.cursor/mcp.json` or `~/.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "home-browser": {
      "command": "ssh",
      "args": [
        "user@100.x.y.z",
        "/path/to/home-browser-mcp/.venv/bin/scrapling-mcp"
      ]
    }
  }
}
```

### Claude Desktop (`claude_desktop_config.json`)
```json
{
  "mcpServers": {
    "home-browser": {
      "command": "ssh",
      "args": [
        "user@100.x.y.z",
        "/path/to/home-browser-mcp/.venv/bin/scrapling-mcp"
      ]
    }
  }
}
```

### Claude Code CLI
```bash
claude mcp add home-browser -- ssh user@100.x.y.z "/path/to/home-browser-mcp/.venv/bin/scrapling-mcp"
```

---

## Troubleshooting & FAQ

- **`ssh` asks for a password**: Configure SSH key authentication (`ssh-copy-id user@home-pc`). MCP clients and bot runners cannot type interactive passwords.
- **Run diagnostics**: Execute `./hbm test` on your home computer to instantly pinpoint whether Tailscale, SSH, or browser binaries need attention.
- **Security**: Traffic travels strictly over encrypted, peer-to-peer Tailscale connections. No open ports on your home router are needed.
