#!/usr/bin/env python3
"""
Audit ~/Dev projects against the gold standard template (DocKit format).

Checks: README structure, badges, screenshots, gitignore, dependency pinning.

Usage:
    python3 repo_audit.py                    # audit all projects
    python3 repo_audit.py cc-harness dockit  # audit specific projects
    python3 repo_audit.py --fix-gitignore    # audit + auto-fix gitignore gaps
"""

import re
import sys
from pathlib import Path

DEV = Path.home() / "Dev"

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────

# Projects to audit (skip private/experimental ones)
SKIP = {"configs", "hydro-app-tauri", ".claude", ".DS_Store"}

GITIGNORE_BASELINE = {
    "# Python": ["__pycache__/", "*.py[cod]", "*.egg-info/", "dist/", "build/", "*.egg"],
    "# Virtual env": [".venv/", "venv/"],
    "# Environment": [".env"],
    "# IDE": [".idea/", ".vscode/"],
    "# OS": [".DS_Store"],
    "# Cache": [".pytest_cache/", ".ruff_cache/", ".mypy_cache/"],
}


# ─────────────────────────────────────────────
# Checkers
# ─────────────────────────────────────────────

def check_readme(project_dir: Path, lang: str = "en") -> list[str]:
    """Check README against gold standard template. Returns list of issues."""
    fname = "README.md" if lang == "en" else "README_CN.md"
    path = project_dir / fname
    issues = []

    if not path.exists():
        issues.append(f"Missing {fname}")
        return issues

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # 1. Language selector
    if lang == "en":
        if not any("**English**" in l and "中文" in l for l in lines[:5]):
            issues.append(f"{fname}: missing language selector (expected '**English** | [中文](README_CN.md)')")
    else:
        if not any("**中文**" in l and "English" in l for l in lines[:5]):
            issues.append(f"{fname}: missing language selector (expected '[English](README.md) | **中文**')")

    # 2. Badge style
    badge_lines = [l for l in lines if "img.shields.io/badge" in l]
    non_ftb = [l for l in badge_lines if "style=for-the-badge" not in l]
    if non_ftb:
        issues.append(f"{fname}: {len(non_ftb)} badge(s) not using for-the-badge style")

    # 3. Separator after badges
    if badge_lines:
        last_badge_idx = max(i for i, l in enumerate(lines) if "img.shields.io/badge" in l)
        # Look for --- within 3 lines after last badge
        found_sep = any(lines[j].strip() == "---" for j in range(last_badge_idx + 1, min(last_badge_idx + 4, len(lines))))
        if not found_sep:
            issues.append(f"{fname}: missing separator '---' after badges")

    # 4. Screenshot
    has_screenshot = any(re.search(r"!\[.*\]\(docs/screenshots/", l) for l in lines)
    if not has_screenshot:
        issues.append(f"{fname}: missing screenshot reference (docs/screenshots/)")

    # 5. Screenshot file exists
    if has_screenshot:
        screenshot_path = project_dir / "docs" / "screenshots" / "demo.png"
        homepage_path = project_dir / "docs" / "screenshots" / "homepage.png"
        if not screenshot_path.exists() and not homepage_path.exists():
            issues.append(f"{fname}: screenshot referenced but file not found in docs/screenshots/")

    # 6. Feature table
    has_table = any(l.strip().startswith("|") and "---" not in l and "|" in l[1:] for l in lines)
    if not has_table:
        issues.append(f"{fname}: missing feature table")

    # 7. Install section
    has_install = any(re.match(r"^#{1,3}\s*(Install|安装)", l) for l in lines)
    if not has_install:
        issues.append(f"{fname}: missing Install/安装 section")

    # 8. Quick Start section
    has_quickstart = any(re.match(r"^#{1,3}\s*(Quick Start|快速|Usage|使用|快速上手)", l) for l in lines)
    if not has_quickstart:
        issues.append(f"{fname}: missing Quick Start section")

    return issues


def check_gitignore(project_dir: Path) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Check .gitignore for baseline entries. Returns (issues, missing_sections)."""
    path = project_dir / ".gitignore"
    issues = []
    missing_sections = []

    if not path.exists():
        issues.append("Missing .gitignore")
        return issues, []

    content = path.read_text(encoding="utf-8")
    existing = set()
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing.add(stripped.rstrip("/"))

    for section, entries in GITIGNORE_BASELINE.items():
        section_missing = []
        for entry in entries:
            normalized = entry.rstrip("/")
            if normalized not in existing:
                section_missing.append(entry)
        if section_missing:
            missing_sections.append((section, section_missing))
            issues.append(f".gitignore: missing {len(section_missing)} entries from {section}")

    return issues, missing_sections


def check_deps(project_dir: Path) -> list[str]:
    """Check dependency version pinning."""
    issues = []
    req_path = project_dir / "requirements.txt"

    if req_path.exists():
        for line in req_path.read_text().strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            if ">=" not in line and "==" not in line and "~=" not in line:
                issues.append(f"requirements.txt: unpinned dependency '{line}'")

    return issues


def fix_gitignore(project_dir: Path, missing_sections: list[tuple[str, list[str]]]):
    """Append missing gitignore entries."""
    path = project_dir / ".gitignore"
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"

    append_lines = ["\n"]
    for comment, entries in missing_sections:
        append_lines.append(comment)
        for e in entries:
            append_lines.append(e)
        append_lines.append("")

    content += "\n".join(append_lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


# ─────────────────────────────────────────────
# Reporter
# ─────────────────────────────────────────────

def audit_project(name: str, fix: bool = False) -> list[str]:
    """Run all checks on a single project. Returns list of issues."""
    project_dir = DEV / name
    if not project_dir.is_dir():
        return [f"Directory not found: {project_dir}"]

    all_issues = []

    # Detect project type
    has_python = any(project_dir.glob("*.py")) or (project_dir / "requirements.txt").exists()

    if has_python:
        # README checks
        all_issues.extend(check_readme(project_dir, "en"))
        all_issues.extend(check_readme(project_dir, "cn"))

        # Gitignore
        gi_issues, missing_sections = check_gitignore(project_dir)
        all_issues.extend(gi_issues)
        if fix and missing_sections:
            fix_gitignore(project_dir, missing_sections)
            all_issues.append(f".gitignore: ✓ FIXED ({sum(len(s) for _, s in missing_sections)} entries added)")

        # Dependencies
        all_issues.extend(check_deps(project_dir))

    return all_issues


def main():
    fix_gi = "--fix-gitignore" in sys.argv
    targets = [a for a in sys.argv[1:] if not a.startswith("--")]

    if not targets:
        # Auto-discover projects
        targets = sorted(
            d.name for d in DEV.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name not in SKIP
        )

    total_issues = 0
    clean_count = 0

    for name in targets:
        issues = audit_project(name, fix=fix_gi)
        if not issues:
            clean_count += 1
            continue

        print(f"\n{'─'*50}")
        print(f"  {name}")
        print(f"{'─'*50}")
        for issue in issues:
            marker = "  ✓" if "FIXED" in issue else "  ✗"
            print(f"{marker} {issue}")
        total_issues += len([i for i in issues if "FIXED" not in i])

    print(f"\n{'='*50}")
    print(f"Audited {len(targets)} projects: {clean_count} clean, {total_issues} issues found")
    if fix_gi:
        print(f"(--fix-gitignore applied)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
