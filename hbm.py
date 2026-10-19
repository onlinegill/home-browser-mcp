#!/usr/bin/env python3
"""Home-Browser MCP (HBM) — One-Click Automated Tool

Unified CLI and Python client for browsing through your home residential IP,
bypassing datacenter blocks, Cloudflare Turnstile, and anti-bot walls for
Muse, Groq bots, and AI assistants.

Usage:
  ./hbm setup                Auto-install dependencies, browser binaries, check Tailscale & SSH
  ./hbm test                 Run complete self-diagnostics
  ./hbm info                 Show Tailscale IP, SSH status, and bot config snippets
  ./hbm fetch <url>          One-line stealth fetch (bypasses Cloudflare, returns LLM Markdown)
  ./hbm drive                Execute a JSON plan of MCP steps (pipe via stdin)
  ./hbm serve                Run Scrapling or Playwright MCP server directly

Python SDK for Muse & Groq bots:
  from hbm import HomeBrowser
  hb = HomeBrowser(host="user@home-tailscale-ip")
  markdown = hb.fetch_markdown("https://example.com")
"""
import argparse
import asyncio
import json
import os
import re
import shlex
import shutil
import subprocess
import sys

MAX_OUT = 8000
SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
VENV_DIR = os.path.join(SCRIPT_DIR, ".venv")
VENV_BIN = os.path.join(VENV_DIR, "bin")
VENV_PYTHON = os.path.join(VENV_BIN, "python")
DEFAULT_PROFILE_DIR = os.path.expanduser("~/.home-browser-profile")

# Tailscale & System Utilities
# =====================================================================

def get_tailscale_ip() -> str | None:
    """Retrieve the local machine's Tailscale IPv4 address."""
    try:
        res = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, check=True)
        return res.stdout.strip().splitlines()[0]
    except Exception:
        return None


def get_current_user() -> str:
    import getpass
    return getpass.getuser()


def check_ssh_service() -> bool:
    """Check if local SSH server is listening on port 22."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    try:
        s.connect(("127.0.0.1", 22))
        s.close()
        return True
    except Exception:
        return False


# =====================================================================
# Setup Command (One-Click Auto Setup)
# =====================================================================

def cmd_setup(args):
    print("=" * 60)
    print("  Home-Browser MCP — Automated One-Click Setup")
    print("=" * 60)

    # 1. Virtual environment setup
    print("\n[1/5] Checking Python virtual environment...")
    python_exe = sys.executable
    venv_ok = os.path.exists(VENV_PYTHON) and subprocess.run([VENV_PYTHON, "-m", "pip", "--version"], capture_output=True).returncode == 0
    if not venv_ok:
        print(f"Creating virtual environment in {VENV_DIR}...")
        if os.path.exists(VENV_DIR):
            shutil.rmtree(VENV_DIR, ignore_errors=True)
        try:
            subprocess.run([python_exe, "-m", "venv", VENV_DIR], check=True)
        except subprocess.CalledProcessError:
            print("\n❌ Failed to create virtual environment.")
            print("On Debian/Ubuntu/Proxmox, you need to install python3-venv:")
            print("    apt install -y python3-venv python3-pip\n")
            sys.exit(1)
    else:
        print(f"Using existing virtual environment at {VENV_DIR}")

    pip_cmd = [VENV_PYTHON, "-m", "pip", "install", "--upgrade", "pip"]
    subprocess.run(pip_cmd, check=False)

    # 2. Install requirements
    print("\n[2/5] Installing Python dependencies (MCP + Scrapling Stealth)...")
    req_file = os.path.join(SCRIPT_DIR, "requirements.txt")
    if os.path.exists(req_file):
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "-r", req_file], check=True)
    else:
        subprocess.run([VENV_PYTHON, "-m", "pip", "install", "mcp>=1.3.0", "scrapling[ai]>=0.4.15"], check=True)

    # 3. Install browser binaries for Scrapling
    print("\n[3/5] Installing browser dependencies for Scrapling...")
    scrapling_bin = os.path.join(VENV_BIN, "scrapling")
    if os.path.exists(scrapling_bin):
        subprocess.run([scrapling_bin, "install"], check=True)

    # 4. Optional Playwright MCP installation (if npm is available)
    print("\n[4/5] Checking Node.js / Playwright MCP...")
    if shutil.which("npm"):
        try:
            print("Installing @playwright/mcp globally or via npx...")
            subprocess.run(["npx", "-y", "--package=@playwright/mcp@latest", "playwright", "install", "chromium"], check=True)
            print("Playwright Chromium browser installed.")
        except Exception as e:
            print(f"Note: Playwright installation had notice (non-fatal): {e}")
    else:
        print("npm not detected; Scrapling Stealth engine is ready (Node.js optional).")

    # 5. Tailscale & SSH Verification
    print("\n[5/5] Checking Tailscale & SSH...")
    ts_ip = get_tailscale_ip()
    user = get_current_user()
    ssh_ok = check_ssh_service()

    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)

    if ts_ip:
        print(f" Tailscale IP:  {ts_ip}")
        print(f" SSH Target:    {user}@{ts_ip}")
    else:
        print(" Tailscale:     Not detected or not logged in. Run 'tailscale up' to connect.")

    print(f" SSH Service:   {'Running (Port 22 open)' if ssh_ok else 'Port 22 not responding (Enable Remote Login / sshd)'}")
    print("\n" + "-" * 60)
    print("  Configuration Snippets for Your AI Assistants / Bots")
    print("-" * 60)

    host_target = f"{user}@{ts_ip if ts_ip else '<home-pc-tailscale-ip>'}"

    print("\n[For Muse & Groq Python Bots]")
    print(f"""from hbm import HomeBrowser

hb = HomeBrowser(host="{host_target}")
# Automatically bypasses Cloudflare and returns clean LLM Markdown:
markdown = hb.fetch_markdown("https://example.com")
print(markdown)
""")

    print("\n[For Claude Desktop (claude_desktop_config.json)]")
    desktop_cfg = {
        "mcpServers": {
            "home-stealth": {
                "command": "ssh",
                "args": [host_target, f"{VENV_BIN}/scrapling-mcp"]
            }
        }
    }
    print(json.dumps(desktop_cfg, indent=2))

    print("\n[For Claude Code CLI]")
    print(f'claude mcp add home-stealth -- ssh {host_target} "{VENV_BIN}/scrapling-mcp"')
    print("-" * 60 + "\n")


# =====================================================================
# Info Command
# =====================================================================

def cmd_info(args):
    ts_ip = get_tailscale_ip()
    user = get_current_user()
    ssh_ok = check_ssh_service()
    host_target = f"{user}@{ts_ip if ts_ip else '<home-pc-tailscale-ip>'}"

    print(json.dumps({
        "tailscale_ip": ts_ip,
        "username": user,
        "ssh_target": host_target,
        "ssh_listening": ssh_ok,
        "scrapling_mcp_path": os.path.join(VENV_BIN, "scrapling-mcp"),
        "python_path": VENV_PYTHON
    }, indent=2))


# =====================================================================
# Fetch Command (One-Click CLI Fetch)
# =====================================================================

def cmd_fetch(args):
    """Fetch a URL using local or remote Scrapling."""
    url = args.url
    solve_cf = not args.no_cloudflare
    as_markdown = not args.raw

    hb = HomeBrowser(host=args.host, engine=args.engine)
    if as_markdown:
        res = hb.fetch_markdown(url, solve_cloudflare=solve_cf)
        print(res)
    else:
        res = hb.fetch(url, solve_cloudflare=solve_cf)
        print(json.dumps(res, indent=2))


# =====================================================================
# Login Command (Persistent Session & 2FA Setup)
# =====================================================================

def cmd_login(args):
    """Open visible browser on this machine so user can log into Amazon/sites and save session."""
    url = args.url or "https://www.amazon.com"
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    profile_dir = os.path.expanduser(args.profile_dir)
    os.makedirs(profile_dir, exist_ok=True)

    print("=" * 60)
    print(f"  Opening Visible Browser for Login: {url}")
    print("=" * 60)
    print(f"Profile directory: {profile_dir}")
    print("\n👉 Log into your account (Amazon, etc.), solve any 2FA/SMS codes,")
    print("   and then simply CLOSE the browser window when finished.\n")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_dir,
            headless=False,
            channel="chrome" if os.path.exists("/Applications/Google Chrome.app") else None,
            args=["--no-first-run", "--no-default-browser-check"]
        )
        page = context.new_page() if not context.pages else context.pages[0]
        page.goto(url)
        print("Waiting for browser window to be closed...")
        try:
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
        context.close()

    print("\n✅ Success! Your login session and cookies are saved in ~/.home-browser-profile.")
    print("   Muse and other bots will now automatically use your logged-in session!\n")


# =====================================================================
# Test Diagnostics Command
# =====================================================================

def cmd_test(args):
    print("Running Home-Browser MCP Self-Diagnostics...\n")
    ts_ip = get_tailscale_ip()
    print(f"1. Tailscale Status:   {'OK (' + ts_ip + ')' if ts_ip else 'FAIL (Run tailscale up)'}")
    ssh_ok = check_ssh_service()
    print(f"2. Local SSH Service:  {'OK (listening)' if ssh_ok else 'WARNING (enable SSH server)'}")

    scrapling_bin = os.path.join(VENV_BIN, "scrapling-mcp")
    if not os.path.exists(scrapling_bin):
        scrapling_bin = shutil.which("scrapling-mcp")

    print(f"3. Scrapling MCP:      {'OK (' + str(scrapling_bin) + ')' if scrapling_bin else 'FAIL (Run ./hbm setup)'}")

    if scrapling_bin:
        print("\n4. Testing Live Stealth Fetch on https://example.com...")
        hb = HomeBrowser(engine="scrapling")
        try:
            content = hb.fetch_markdown("https://example.com")
            if "Example Domain" in content or "documentation" in content:
                print("   Result: SUCCESS! Page fetched and converted to Markdown.")
            else:
                print(f"   Result: Output received ({len(content)} chars).")
        except Exception as e:
            print(f"   Result: FAILED ({e})")

    print("\nSelf-diagnostics complete.")


# =====================================================================
# MCP Driver Engine (mcp_drive.py compatibility)
# =====================================================================

def build_ref_map(text: str) -> dict:
    """Parse Playwright MCP snapshot into {(role, name): ref}."""
    refs = {}
    for m in re.finditer(r'-\s+(\w+)\s+"([^"]+)"[^\n]*?\[ref=([^\]]+)\]', text):
        refs[(m.group(1), m.group(2))] = m.group(3)
    return refs


def summarize_blocks(content) -> str:
    """Flatten MCP content blocks to text."""
    parts = []
    for block in content:
        t = getattr(block, "type", "")
        if t == "text":
            parts.append(block.text)
        elif t == "image":
            mime = getattr(block, "mime_type", getattr(block, "mimeType", "image"))
            parts.append(f"[image {mime}]")
        else:
            parts.append(f"[{t}]")
    return "\n".join(parts)


def truncate_text(text: str, limit: int = MAX_OUT) -> str:
    return text[:limit] + ("...[truncated]" if len(text) > limit else "")


def resolve_server_cmd(cmd_arg: str | None = None, host: str | None = None, engine: str = "scrapling") -> list[str]:
    if cmd_arg:
        return shlex.split(cmd_arg)
    if os.environ.get("HBM_CMD"):
        return shlex.split(os.environ["HBM_CMD"])

    host = host or os.environ.get("HBM_SSH_HOST")
    engine = os.environ.get("HBM_ENGINE", engine).lower()

    if host:
        if engine in ("scrapling", "stealth"):
            return ["ssh", host, "scrapling-mcp"]
        base = ["ssh", host, "npx", "-y", "@playwright/mcp", "--headless"]
        if os.path.exists(DEFAULT_PROFILE_DIR):
            base.extend(["--user-data-dir", "~/.home-browser-profile"])
        return base

    # Local fallback
    if engine in ("scrapling", "stealth"):
        scrapling_bin = os.path.join(VENV_BIN, "scrapling-mcp")
        if os.path.exists(scrapling_bin):
            return [scrapling_bin]
        return ["scrapling-mcp"]
    base = ["npx", "-y", "@playwright/mcp", "--headless"]
    if os.path.exists(DEFAULT_PROFILE_DIR):
        base.extend(["--user-data-dir", DEFAULT_PROFILE_DIR])
    return base


async def run_mcp_plan(plan: list[dict], cmd: list[str]) -> list[dict]:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    extra_env = {k: v for k, v in os.environ.items() if "proxy" in k.lower()}
    params = StdioServerParameters(command=cmd[0], args=cmd[1:], env=extra_env)
    results = []
    ref_map = {}

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for step in plan:
                name = step["tool"]
                args = dict(step.get("args", {}))

                if "ref_lookup" in args:
                    want = args.pop("ref_lookup")
                    key = (want.get("role"), want.get("name"))
                    ref = ref_map.get(key)
                    if ref is None:
                        results.append({"tool": name, "ok": False,
                                        "output": f"ERROR: no ref for {key}; run browser_snapshot first"})
                        continue
                    args["target"] = ref
                    args.setdefault("element", f"{key[0]} {key[1]}".strip())

                try:
                    res = await session.call_tool(name, args)
                    out = summarize_blocks(res.content)
                    if name == "browser_snapshot" and not res.is_error:
                        ref_map = build_ref_map(out)
                    results.append({"tool": name, "ok": not res.is_error, "output": out})
                except Exception as e:
                    results.append({"tool": name, "ok": False, "output": f"ERROR: {e}"[:500]})
    return results


def cmd_drive(args):
    cmd = resolve_server_cmd(cmd_arg=args.cmd, host=args.host, engine=args.engine)
    plan = json.load(sys.stdin)
    results = asyncio.run(run_mcp_plan(plan, cmd))
    out = {"results": results}

    if args.out:
        with open(args.out, "w") as f:
            json.dump(out, f, indent=2)
        print(f"wrote {args.out} ({len(json.dumps(out))} bytes)")
    elif getattr(args, "full", False) or not sys.stdout.isatty():
        print(json.dumps(out, indent=2))
    else:
        short = {"results": [{**r, "output": truncate_text(r["output"])} for r in results]}
        print(json.dumps(short, indent=2))


# =====================================================================
# Python SDK Class for Muse & Groq Bots
# =====================================================================

class HomeBrowser:
    """Python client for Muse, Groq, and AI bots to browse via home IP."""

    def __init__(self, host: str | None = None, engine: str = "scrapling", cmd: str | None = None):
        self.host = host or os.environ.get("HBM_SSH_HOST")
        self.engine = engine
        self.cmd = cmd

    def execute_plan(self, plan: list[dict]) -> list[dict]:
        server_cmd = resolve_server_cmd(cmd_arg=self.cmd, host=self.host, engine=self.engine)
        try:
            from mcp import ClientSession
            return asyncio.run(run_mcp_plan(plan, server_cmd))
        except ImportError:
            if os.path.exists(VENV_PYTHON):
                proc = subprocess.run(
                    [VENV_PYTHON, os.path.join(SCRIPT_DIR, "hbm.py"), "drive", "--full"],
                    input=json.dumps(plan),
                    text=True,
                    capture_output=True,
                    check=True
                )
                stdout = proc.stdout
                start = stdout.find("{")
                if start != -1:
                    stdout = stdout[start:]
                return json.loads(stdout).get("results", [])
            raise

    def fetch(self, url: str, extraction_type: str = "markdown", solve_cloudflare: bool = True, wait: int | None = None, network_idle: bool = True) -> dict:
        """Fetch URL with Scrapling stealth, returning raw result data."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        # Amazon and dynamic sites serve a 202 JS handshake that requires network settle:
        if wait is None and "amazon." in url.lower():
            wait = 2000

        args = {
            "url": url,
            "extraction_type": extraction_type,
            "solve_cloudflare": solve_cloudflare,
            "network_idle": network_idle
        }
        if wait:
            args["wait"] = wait

        # Scrapling >= 0.5 renamed tool to 'browser_fetch_once' (was 'stealthy_fetch' in 0.4.x)
        plan = [{"tool": "browser_fetch_once", "args": args}]
        res = self.execute_plan(plan)
        if not res or not res[0].get("ok"):
            err_msg = str(res[0].get("output") if res else "")
            if "Unknown tool" in err_msg or "not found" in err_msg:
                plan = [{"tool": "stealthy_fetch", "args": args}]
                res = self.execute_plan(plan)

        if not res or not res[0].get("ok"):
            err = res[0].get("output") if res else "Unknown error"
            raise RuntimeError(f"Fetch failed: {err}")
        try:
            return json.loads(res[0]["output"])
        except Exception:
            return {"raw": res[0]["output"]}

    def fetch_markdown(self, url: str, solve_cloudflare: bool = True, wait: int | None = None, network_idle: bool = True) -> str:
        """Fetch URL and return clean LLM Markdown string."""
        data = self.fetch(url, extraction_type="markdown", solve_cloudflare=solve_cloudflare, wait=wait, network_idle=network_idle)
        content = data.get("content", [])
        if isinstance(content, list):
            return "\n\n".join(str(c) for c in content if c)
        return str(content)


# =====================================================================
# Main CLI Entrypoint
# =====================================================================

def main():
    # Auto re-exec inside local .venv if not already active
    if sys.prefix == sys.base_prefix and os.path.exists(VENV_PYTHON):
        if len(sys.argv) < 2 or sys.argv[1] != "setup":
            os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

    parser = argparse.ArgumentParser(
        prog="hbm",
        description="Home-Browser MCP: One-Click Tool for residential IP browsing, Cloudflare bypass & MCP"
    )
    subparsers = parser.add_subparsers(dest="command")

    # setup
    subparsers.add_parser("setup", help="Auto-install all dependencies and browsers on home PC")

    # info
    subparsers.add_parser("info", help="Display Tailscale IP and connection info")

    # test
    subparsers.add_parser("test", help="Run self-diagnostics")

    # fetch
    fetch_parser = subparsers.add_parser("fetch", help="Fetch a URL with Scrapling stealth through home IP")
    fetch_parser.add_argument("url", help="URL to fetch")
    fetch_parser.add_argument("--host", default=None, help="SSH target (e.g. user@home-pc)")
    fetch_parser.add_argument("--engine", default="scrapling", help="Engine to use (scrapling or playwright)")
    fetch_parser.add_argument("--no-cloudflare", action="store_true", help="Disable Cloudflare auto-solver")
    fetch_parser.add_argument("--raw", action="store_true", help="Output full JSON instead of Markdown")

    # drive
    drive_parser = subparsers.add_parser("drive", help="Execute an MCP plan from stdin")
    drive_parser.add_argument("--cmd", default=None, help="Custom server command")
    drive_parser.add_argument("--host", default=None, help="SSH host target")
    drive_parser.add_argument("--engine", default="scrapling", help="Engine (scrapling or playwright)")
    drive_parser.add_argument("--out", default=None, help="File to write full JSON results")
    drive_parser.add_argument("--full", action="store_true", help="Output full JSON without truncation")

    # login
    login_parser = subparsers.add_parser("login", help="Open visible browser to log into Amazon/sites and save session")
    login_parser.add_argument("url", nargs="?", default="https://www.amazon.com", help="URL to log into (default: amazon.com)")
    login_parser.add_argument("--profile-dir", default=DEFAULT_PROFILE_DIR, help="Path to persistent browser profile")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Run the MCP server directly")
    serve_parser.add_argument("--engine", default="scrapling", choices=["scrapling", "playwright"])

    # If no args or piped stdin without subcmd, default behavior
    if len(sys.argv) == 1:
        if not sys.stdin.isatty():
            # Piped input: default to drive
            sys.argv.insert(1, "drive")
        else:
            parser.print_help()
            sys.exit(0)

    # Legacy support: if flags like --cmd or --out or --engine are passed at top level
    if sys.argv[1].startswith("-") and sys.argv[1] not in ("-h", "--help"):
        sys.argv.insert(1, "drive")

    parsed = parser.parse_args()

    if parsed.command == "setup":
        cmd_setup(parsed)
    elif parsed.command == "login":
        cmd_login(parsed)
    elif parsed.command == "info":
        cmd_info(parsed)
    elif parsed.command == "test":
        cmd_test(parsed)
    elif parsed.command == "fetch":
        cmd_fetch(parsed)
    elif parsed.command == "drive":
        cmd_drive(parsed)
    elif parsed.command == "serve":
        if parsed.engine == "scrapling":
            scrapling_bin = os.path.join(VENV_BIN, "scrapling-mcp")
            os.execv(scrapling_bin if os.path.exists(scrapling_bin) else "scrapling-mcp", ["scrapling-mcp"])
        else:
            npx_bin = shutil.which("npx")
            if not npx_bin:
                sys.exit("npm/npx not found")
            os.execv(npx_bin, ["npx", "-y", "@playwright/mcp", "--headless"])
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
