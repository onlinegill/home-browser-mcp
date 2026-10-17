#!/usr/bin/env python3
"""MCP driver shim for AI bots/agents WITHOUT native MCP support.

Spawns an MCP server (Playwright or Scrapling Stealth) over SSH stdio, executes
a plan of MCP tool calls, and prints results as JSON. Any bot that can run a
subprocess and parse JSON (Muse, Groq bots, custom agents) can drive a home-IP
browser this way.

Supported engines:
  - playwright (default): Interactive automation (click, type, navigate, snapshot).
  - scrapling: Anti-bot bypass (Cloudflare Turnstile, stealthy fetch, LLM markdown).

Server command resolution (first match wins):
  1. --cmd "..." argument
  2. HBM_CMD environment variable
  3. HBM_SSH_HOST env with HBM_ENGINE:
     - HBM_ENGINE=scrapling  -> "ssh $HBM_SSH_HOST scrapling-mcp"
     - HBM_ENGINE=playwright -> "ssh $HBM_SSH_HOST npx -y @playwright/mcp --headless"

Examples:
  # Scrapling Stealth (bypasses Cloudflare / Turnstile to clean Markdown):
  HBM_SSH_HOST=user@home-pc.tailxxx.ts.net HBM_ENGINE=scrapling
  echo '[{"tool":"stealthy_fetch","args":{"url":"https://example.com","extraction_type":"markdown"}}]' | mcp_drive.py

  # Playwright (interactive browser automation):
  HBM_SSH_HOST=user@home-pc.tailxxx.ts.net
  echo '[{"tool":"browser_navigate","args":{"url":"https://example.com"}},
         {"tool":"browser_snapshot","args":{}}]' | mcp_drive.py

Full output goes to --out <file>; stdout is truncated per step.
Requires: pip install -r requirements.txt
"""
import asyncio
import json
import os
import shlex
import sys

MAX_OUT = 8000
_SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
_VENV_PYTHON = os.path.join(_SCRIPT_DIR, ".venv", "bin", "python")
if sys.prefix == sys.base_prefix and os.path.exists(_VENV_PYTHON):
    os.execv(_VENV_PYTHON, [_VENV_PYTHON] + sys.argv)


def server_command():
    if "--cmd" in sys.argv:
        return shlex.split(sys.argv[sys.argv.index("--cmd") + 1])
    if os.environ.get("HBM_CMD"):
        return shlex.split(os.environ["HBM_CMD"])
    host = os.environ.get("HBM_SSH_HOST")
    if not host:
        raise SystemExit("set --cmd, HBM_CMD, or HBM_SSH_HOST")
    engine = os.environ.get("HBM_ENGINE", "playwright").lower()
    if "--engine" in sys.argv:
        engine = sys.argv[sys.argv.index("--engine") + 1].lower()
    if engine in ("scrapling", "stealth"):
        return ["ssh", host, "scrapling-mcp"]
    return ["ssh", host, "npx", "-y", "@playwright/mcp", "--headless"]


def build_ref_map(text):
    """Parse an MCP snapshot into {(role, name): ref}."""
    import re
    refs = {}
    for m in re.finditer(r'-\s+(\w+)\s+"([^"]+)"[^\n]*?\[ref=([^\]]+)\]', text):
        refs[(m.group(1), m.group(2))] = m.group(3)
    return refs


def summarize(content):
    """Flatten MCP content blocks to text (full, untruncated)."""
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


def truncate(text, limit=MAX_OUT):
    return text[:limit] + ("...[truncated]" if len(text) > limit else "")


async def run(plan, cmd):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    # The MCP SDK only inherits an allowlisted env; pass proxy vars through
    # explicitly (needed when the server command itself uses a proxy).
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
                # Resolve {"ref_lookup": {"role":..., "name":...}} against the
                # most recent snapshot (refs live only within one run).
                if "ref_lookup" in args:
                    want = args.pop("ref_lookup")
                    key = (want.get("role"), want.get("name"))
                    ref = ref_map.get(key)
                    if ref is None:
                        results.append({"tool": name, "ok": False,
                                        "output": f"ERROR: no ref for {key}; "
                                                  "run browser_snapshot first"})
                        continue
                    # @playwright/mcp takes the snapshot ref as "target".
                    args["target"] = ref
                    args.setdefault("element", f"{key[0]} {key[1]}".strip())
                try:
                    res = await session.call_tool(name, args)
                    out = summarize(res.content)
                    if name == "browser_snapshot" and not res.is_error:
                        ref_map = build_ref_map(out)
                    results.append({"tool": name, "ok": not res.is_error,
                                    "output": out})
                except Exception as e:  # noqa: BLE001
                    results.append({"tool": name, "ok": False,
                                    "output": f"ERROR: {e}"[:500]})
    return results


def main():
    cmd = server_command()
    plan = json.load(sys.stdin)
    results = asyncio.run(run(plan, cmd))
    out = {"results": results}
    if "--out" in sys.argv:
        path = sys.argv[sys.argv.index("--out") + 1]
        with open(path, "w") as f:
            json.dump(out, f, indent=1)
        print(f"wrote {path} ({len(json.dumps(out))} bytes)")
    else:
        short = {"results": [
            {**r, "output": truncate(r["output"])} for r in results]}
        print(json.dumps(short, indent=1))


if __name__ == "__main__":
    main()
