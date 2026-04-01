#!/usr/bin/env python3
"""批量 commit + push 所有 auto_push 仓库，用智谱 GLM 生成 commit message。

repo 列表从 ~/Dev/configs/repo-map.json 读取（auto_push: true 的条目）。

用法:
    python3 git_smart_push.py           # AI 生成 commit message
    python3 git_smart_push.py --simple  # 简单 message（给 launchd 用）
    python3 git_smart_push.py --all     # 推所有 repo（不限 auto_push）
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.llm_client import chat as llm_chat

REPO_MAP = Path.home() / "Dev/configs/repo-map.json"

SYSTEM_PROMPT = (
    "你是 Git commit message 生成器。根据 diff 生成一行简洁的中文 commit message。"
    "规则：不超过50字，不要引号，不要前缀（如 feat:/fix:），直接描述改了什么。"
    "如果改动太杂，用「更新多个文件」概括。"
)

MAX_DIFF_CHARS = 3000


def load_repos(all_repos: bool = False) -> list[Path]:
    """从 repo-map.json 读取 repo 路径列表。"""
    with open(REPO_MAP) as f:
        data = json.load(f)

    repos = []
    for name, info in data["repos"].items():
        if all_repos or info.get("auto_push", False):
            local = Path(info["local"]).expanduser()
            repos.append(local)

    # 始终包含 ~/.claude（不在 registry 中，但需要 auto-push）
    claude_dir = Path.home() / ".claude"
    if claude_dir.is_dir() and (claude_dir / ".git").is_dir():
        repos.append(claude_dir)

    return sorted(repos)


def run(cmd: list[str], cwd: Path) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
    return r.stdout.strip()


def has_changes(repo: Path) -> bool:
    return bool(run(["git", "status", "--porcelain"], repo))


def get_diff_summary(repo: Path) -> str:
    diff = run(["git", "diff", "--cached", "--stat"], repo)
    diff_content = run(["git", "diff", "--cached"], repo)
    if not diff_content:
        return run(["git", "status", "--short"], repo)[:MAX_DIFF_CHARS]
    if len(diff_content) > MAX_DIFF_CHARS:
        return diff + "\n\n" + diff_content[:MAX_DIFF_CHARS] + "\n...(truncated)"
    return diff + "\n\n" + diff_content


def generate_message(diff: str) -> str:
    try:
        msg = llm_chat(SYSTEM_PROMPT, diff, provider="zhipu")
        return msg.strip().strip('"').strip("'").split("\n")[0][:80]
    except Exception as e:
        print(f"  AI 生成失败: {e}，使用 fallback")
        return None


def simple_message() -> str:
    return f"sync: {datetime.now().strftime('%Y-%m-%d %H:%M')}"


def process_repo(repo: Path, use_ai: bool) -> bool:
    name = repo.name if repo.name != ".claude" else ".claude"
    if not (repo / ".git").is_dir():
        return False
    if not has_changes(repo):
        return False

    run(["git", "add", "-A"], repo)
    diff = get_diff_summary(repo)

    if use_ai:
        msg = generate_message(diff)
        if not msg:
            msg = simple_message()
    else:
        msg = simple_message()

    run(["git", "commit", "-m", msg], repo)
    result = subprocess.run(["git", "push"], cwd=repo, capture_output=True, text=True, timeout=60)
    if result.returncode == 0:
        print(f"✅ {name}: {msg}")
        return True
    else:
        print(f"❌ {name}: push failed — {result.stderr.strip()}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simple", action="store_true", help="跳过 AI，用简单 message")
    parser.add_argument("--all", action="store_true", help="推所有 repo（不限 auto_push）")
    args = parser.parse_args()

    use_ai = not args.simple
    repos = load_repos(all_repos=args.all)
    pushed = 0
    skipped = 0

    print(f"扫描 {len(repos)} 个仓库...\n")
    for repo in repos:
        if process_repo(repo, use_ai):
            pushed += 1
        else:
            skipped += 1

    print(f"\n推送完成：{pushed} 个仓库有更新，{skipped} 个无变更")


if __name__ == "__main__":
    main()
