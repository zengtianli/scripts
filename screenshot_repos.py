#!/usr/bin/env python3
"""
Take real Playwright screenshots of live Streamlit demo apps
and update README.md / README_CN.md to use demo.png.

Usage:
    pip install playwright
    playwright install chromium
    python3 screenshot_repos.py [repo_name ...]   # specific repos
    python3 screenshot_repos.py                   # all repos
"""

import subprocess
import sys
import time
from pathlib import Path

DEV = Path.home() / "Dev"

REPOS = {
    "hydro-rainfall":   "https://hydro-rainfall.tianlizeng.cloud",
    "hydro-geocode":    "https://hydro-geocode.tianlizeng.cloud",
    "hydro-district":   "https://hydro-district.tianlizeng.cloud",
    "hydro-irrigation": "https://hydro-irrigation.tianlizeng.cloud",
    "hydro-annual":     "https://hydro-annual.tianlizeng.cloud",
    "hydro-efficiency": "https://hydro-efficiency.tianlizeng.cloud",
    "hydro-reservoir":  "https://hydro-reservoir.tianlizeng.cloud",
    "hydro-capacity":   "https://hydro-capacity.tianlizeng.cloud",
    # CLI tools below use SVG — add URL here if a live demo is added later
    # "hydro-risk":     None,
    # "hydro-qgis":     None,
    # "downloads-organizer": None,
}


def run(cmd: str, cwd: str = None, check: bool = True) -> str:
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{r.stderr}")
    return r.stdout.strip()


def take_screenshot(url: str, out_path: Path) -> bool:
    """Use Playwright to screenshot a Streamlit app."""
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
                # Wait for the main app element
                page.wait_for_selector(".stApp", timeout=20000)
            except Exception:
                pass

            # Extra wait for charts / dynamic content
            time.sleep(3)

            # Hide the Streamlit toolbar/deploy button if present
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


def update_readme_image(readme_path: Path, repo_name: str) -> bool:
    """Replace demo.svg with demo.png in a README file."""
    if not readme_path.exists():
        return False
    content = readme_path.read_text(encoding="utf-8")
    new_content = content.replace(
        f"![{repo_name} demo](docs/screenshots/demo.svg)",
        f"![{repo_name} demo](docs/screenshots/demo.png)",
    )
    if new_content == content:
        return False  # nothing changed
    readme_path.write_text(new_content, encoding="utf-8")
    return True


def process_repo(name: str, url: str) -> bool:
    print(f"\n{'='*55}\n  {name}\n{'='*55}")
    repo_dir = DEV / name

    if not repo_dir.exists():
        print(f"  ✗ Directory not found: {repo_dir}")
        return False

    # Take screenshot
    png_path = repo_dir / "docs" / "screenshots" / "demo.png"
    ok = take_screenshot(url, png_path)
    if not ok:
        return False

    # Update README image references
    changed = False
    for readme in ["README.md", "README_CN.md"]:
        if update_readme_image(repo_dir / readme, name):
            print(f"  ✓ Updated {readme}: demo.svg → demo.png")
            changed = True

    # Commit and push
    run("git add docs/screenshots/demo.png README.md README_CN.md", cwd=str(repo_dir))
    status = run("git status --porcelain", cwd=str(repo_dir))
    if not status:
        print("  ✓ Nothing to commit")
        return True

    run(
        'git commit -m "docs: replace SVG placeholder with real Playwright screenshot\n\n'
        'Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"',
        cwd=str(repo_dir),
    )
    run("git push", cwd=str(repo_dir))
    print("  ✓ Committed and pushed")
    return True


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(REPOS.keys())
    invalid = [t for t in targets if t not in REPOS]
    if invalid:
        print(f"Unknown repos: {invalid}")
        print(f"Available: {list(REPOS.keys())}")
        sys.exit(1)

    total = len(targets)
    success = 0
    for i, name in enumerate(targets, 1):
        print(f"\n[{i}/{total}] {name}")
        if process_repo(name, REPOS[name]):
            success += 1

    print(f"\n{'='*55}")
    print(f"Done: {success}/{total} repos updated")
    print(f"{'='*55}")


if __name__ == "__main__":
    main()
