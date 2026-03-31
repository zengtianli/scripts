#!/usr/bin/env python3
"""
Unified repository screenshot tool — supports Streamlit apps and CLI tools.

Usage:
    # Screenshot a live Streamlit app
    python3 repo_screenshot.py streamlit hydro-rainfall https://hydro-rainfall.tianlizeng.cloud

    # Screenshot a CLI tool by running a command
    python3 repo_screenshot.py cli cc-harness "python3 harness.py ~/Dev/dockit"

    # Screenshot all registered repos (Streamlit only)
    python3 repo_screenshot.py batch

    # Screenshot all repos including CLI tools
    python3 repo_screenshot.py batch --include-cli
"""

import html
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

DEV = Path.home() / "Dev"

# ─────────────────────────────────────────────
# Registry: repos with screenshot configs
# ─────────────────────────────────────────────

REPOS = {
    # Streamlit apps (have live demo URLs)
    "hydro-rainfall":   {"type": "streamlit", "url": "https://hydro-rainfall.tianlizeng.cloud"},
    "hydro-geocode":    {"type": "streamlit", "url": "https://hydro-geocode.tianlizeng.cloud"},
    "hydro-district":   {"type": "streamlit", "url": "https://hydro-district.tianlizeng.cloud"},
    "hydro-irrigation": {"type": "streamlit", "url": "https://hydro-irrigation.tianlizeng.cloud"},
    "hydro-annual":     {"type": "streamlit", "url": "https://hydro-annual.tianlizeng.cloud"},
    "hydro-efficiency": {"type": "streamlit", "url": "https://hydro-efficiency.tianlizeng.cloud"},
    "hydro-reservoir":  {"type": "streamlit", "url": "https://hydro-reservoir.tianlizeng.cloud"},
    "hydro-capacity":   {"type": "streamlit", "url": "https://hydro-capacity.tianlizeng.cloud"},
    "hydro-toolkit":    {"type": "streamlit", "url": "https://hydro.tianlizeng.cloud"},
    "dockit":           {"type": "streamlit", "url": "https://dockit.tianlizeng.cloud"},
    "cclog":            {"type": "streamlit", "url": "https://cclog.tianlizeng.cloud"},

    # CLI tools (run command locally)
    "cc-harness":           {"type": "cli", "cmd": "python3 harness.py {DEV}/dockit", "title": "cc-harness"},
    "cc-context":           {"type": "cli", "cmd": "python3 context.py monitor",       "title": "cc-context"},
    "hydro-risk":           {"type": "cli", "cmd": "python3 01_build_database.py --help 2>&1 || echo 'hydro-risk pipeline'", "title": "hydro-risk"},
    "hydro-qgis":           {"type": "cli", "cmd": "python3 -c \"print('hydro-qgis pipeline')\"", "title": "hydro-qgis"},
    "downloads-organizer":  {"type": "cli", "cmd": "python3 -m downloads_organizer --help 2>&1 || echo 'downloads-organizer'", "title": "downloads-organizer"},
}


# ─────────────────────────────────────────────
# Streamlit screenshot (via Playwright)
# ─────────────────────────────────────────────

def screenshot_streamlit(url: str, out_path: Path) -> bool:
    """Take a Playwright screenshot of a live Streamlit app."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print(f"  Opening {url} ...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=30000)

            # Wait for Streamlit to finish rendering
            try:
                page.wait_for_selector(".stApp", timeout=20000)
            except Exception:
                pass

            # Extra wait for charts / dynamic content
            time.sleep(3)

            # Hide the Streamlit toolbar/deploy button
            page.evaluate("""
                const toolbar = document.querySelector('[data-testid="stToolbar"]');
                if (toolbar) toolbar.style.display = 'none';
                const deploy = document.querySelector('[data-testid="stDecoration"]');
                if (deploy) deploy.style.display = 'none';
            """)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()

        print(f"  ✓ Screenshot saved → {out_path.relative_to(DEV)}")
        return True

    except Exception as e:
        print(f"  ✗ Screenshot failed: {e}")
        return False


# ─────────────────────────────────────────────
# CLI screenshot (terminal-style rendering)
# ─────────────────────────────────────────────

TERMINAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><style>
body {{ margin: 0; padding: 0; background: #0d1117; }}
.terminal {{
    background: #0d1117;
    color: #c9d1d9;
    font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    padding: 20px 24px;
    min-height: 760px;
    box-sizing: border-box;
}}
.titlebar {{
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.dot {{ width: 12px; height: 12px; border-radius: 50%; }}
.dot-red {{ background: #ff5f57; }}
.dot-yellow {{ background: #febc2e; }}
.dot-green {{ background: #28c840; }}
.title {{ color: #8b949e; margin-left: 12px; font-family: -apple-system, sans-serif; font-size: 13px; }}
b {{ color: #f0f6fc; }}
</style></head>
<body>
<div class="titlebar">
    <span class="dot dot-red"></span>
    <span class="dot dot-yellow"></span>
    <span class="dot dot-green"></span>
    <span class="title">{title}</span>
</div>
<pre class="terminal">{content}</pre>
</body>
</html>"""


def colorize_output(raw: str) -> str:
    """Apply terminal-style colors to CLI output."""
    escaped = html.escape(raw)
    colored = escaped
    colored = colored.replace('🔴', '<span style="color:#ff6b6b">🔴</span>')
    colored = colored.replace('🟡', '<span style="color:#ffd93d">🟡</span>')
    colored = colored.replace('🟢', '<span style="color:#6bcb77">🟢</span>')
    colored = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', colored)
    # Markdown headers
    colored = re.sub(
        r'^(#{1,3}) (.+)$',
        lambda m: f'<span style="color:#58a6ff;font-weight:bold">{"#"*len(m.group(1))} {m.group(2)}</span>',
        colored, flags=re.MULTILINE,
    )
    # Table separators
    colored = re.sub(
        r'^(\|[-|: ]+\|)$',
        lambda m: f'<span style="color:#555">{m.group(1)}</span>',
        colored, flags=re.MULTILINE,
    )
    return colored


def screenshot_cli(cmd: str, cwd: str, out_path: Path, title: str = "Terminal") -> bool:
    """Run a CLI command, render output as terminal HTML, screenshot with Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print(f"  Running: {cmd}")
    cmd_expanded = cmd.replace("{DEV}", str(DEV))
    result = subprocess.run(cmd_expanded, shell=True, cwd=cwd, capture_output=True, text=True)
    raw = result.stdout + result.stderr

    if not raw.strip():
        print("  ✗ Command produced no output")
        return False

    colored = colorize_output(raw)
    page_html = TERMINAL_HTML_TEMPLATE.format(title=html.escape(title), content=colored)

    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
        f.write(page_html)
        html_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"file://{html_path}")
            time.sleep(0.5)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()

        print(f"  ✓ Screenshot saved → {out_path.relative_to(DEV)}")
        return True

    except Exception as e:
        print(f"  ✗ Screenshot failed: {e}")
        return False

    finally:
        os.unlink(html_path)


# ─────────────────────────────────────────────
# Unified entry point
# ─────────────────────────────────────────────

def process_repo(name: str, config: dict = None) -> bool:
    """Take screenshot for a single repo using registry config or override."""
    config = config or REPOS.get(name)
    if not config:
        print(f"  ✗ Unknown repo: {name}")
        return False

    repo_dir = DEV / name
    if not repo_dir.exists():
        print(f"  ✗ Directory not found: {repo_dir}")
        return False

    out_path = repo_dir / "docs" / "screenshots" / "demo.png"

    if config["type"] == "streamlit":
        return screenshot_streamlit(config["url"], out_path)
    elif config["type"] == "cli":
        title = config.get("title", name)
        cmd = config["cmd"]
        return screenshot_cli(cmd, str(repo_dir), out_path, f"{title} — {cmd.split()[0]} ...")
    else:
        print(f"  ✗ Unknown type: {config['type']}")
        return False


def update_readme_refs(repo_dir: Path, name: str):
    """Replace demo.svg with demo.png in README files."""
    for readme in ["README.md", "README_CN.md"]:
        path = repo_dir / readme
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"![{name} demo](docs/screenshots/demo.svg)",
            f"![{name} demo](docs/screenshots/demo.png)",
        )
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"  ✓ Updated {readme}: demo.svg → demo.png")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "streamlit":
        # python3 repo_screenshot.py streamlit <repo> <url>
        if len(sys.argv) < 4:
            print("Usage: repo_screenshot.py streamlit <repo-name> <url>")
            sys.exit(1)
        name, url = sys.argv[2], sys.argv[3]
        process_repo(name, {"type": "streamlit", "url": url})
        update_readme_refs(DEV / name, name)

    elif mode == "cli":
        # python3 repo_screenshot.py cli <repo> "<command>"
        if len(sys.argv) < 4:
            print("Usage: repo_screenshot.py cli <repo-name> '<command>'")
            sys.exit(1)
        name, cmd = sys.argv[2], sys.argv[3]
        title = sys.argv[4] if len(sys.argv) > 4 else name
        process_repo(name, {"type": "cli", "cmd": cmd, "title": title})

    elif mode == "batch":
        include_cli = "--include-cli" in sys.argv
        targets = sys.argv[2:] if len(sys.argv) > 2 else list(REPOS.keys())
        targets = [t for t in targets if t != "--include-cli"]

        if not targets:
            targets = list(REPOS.keys())

        total = 0
        success = 0
        for name in targets:
            config = REPOS.get(name)
            if not config:
                continue
            if config["type"] == "cli" and not include_cli:
                continue
            total += 1
            print(f"\n{'='*55}\n  [{total}] {name}\n{'='*55}")
            if process_repo(name, config):
                update_readme_refs(DEV / name, name)
                success += 1

        print(f"\n{'='*55}")
        print(f"Done: {success}/{total} repos screenshotted")
        print(f"{'='*55}")

    else:
        print(f"Unknown mode: {mode}")
        print("Modes: streamlit, cli, batch")
        sys.exit(1)


if __name__ == "__main__":
    main()
