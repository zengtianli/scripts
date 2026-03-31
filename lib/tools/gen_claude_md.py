#!/usr/bin/env python3
"""
批量生成 CLAUDE.md — 调用 claude CLI 为每个项目生成 CLAUDE.md

使用方式：
    python3 lib/tools/gen_claude_md.py                    # 扫描 ~/Dev 所有项目
    python3 lib/tools/gen_claude_md.py hydro-rainfall      # 指定项目
    python3 lib/tools/gen_claude_md.py --force dockit      # 覆盖已有
    python3 lib/tools/gen_claude_md.py --no-commit         # 只生成不 commit
    python3 lib/tools/gen_claude_md.py --dry-run           # 只列出待处理项目
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

DEV_DIR = Path.home() / "Dev"

# 收集项目上下文的最大行数
MAX_README_LINES = 80
MAX_TREE_DEPTH = 2

STYLE_PROMPT = """\
你是一个 Claude Code 配置专家。根据以下项目信息，生成一个 CLAUDE.md 文件。

## 风格要求
- 50-80 行，不超过 100 行
- 实操导向：告诉 Claude 怎么用这个项目，不要复制 README
- 中英文混用（中文描述 + 英文技术术语）
- 必须包含的部分：
  1. 标题行：`# 项目名 — 一句话描述`
  2. Quick Reference 表格：关键路径、入口文件、端口、URL 等
  3. 常用命令（代码块）
  4. 项目结构（如果目录较多）
  5. 凭证位置（如果需要外部 API）：指向 `~/.personal_env`
- 不需要的部分：安装说明、License、贡献指南
- 表格用 markdown 格式
- 代码块标注语言

## 参考风格（oauth-proxy 的 CLAUDE.md）：
```
# CC OAuth Proxy — API 管理平台

## Quick Reference

| 项目 | 路径/值 |
|------|---------|
| 后端 | `oauth_proxy.py` (aiohttp, port 9100) |
| 前端 | `frontend/` (React + Vite + Tailwind) |
| 部署 | `bash deploy.sh` |

## 常用命令
...
```

## 项目信息

{context}

严格要求：
- 直接输出 CLAUDE.md 的 markdown 内容
- 不要加任何解释、确认语句、代码块包裹（如 ```markdown）
- 不要问"需要我写入吗"之类的话
- 第一行必须是 # 标题
- 最后一行必须是内容，不要加 ---
"""


def collect_context(project_dir: Path) -> str:
    """收集项目上下文信息"""
    parts = []

    # 项目名
    parts.append(f"项目名: {project_dir.name}")
    parts.append(f"路径: {project_dir}")

    # README
    for readme in ["README.md", "README_CN.md", "readme.md"]:
        readme_path = project_dir / readme
        if readme_path.exists():
            lines = readme_path.read_text(errors="ignore").splitlines()[:MAX_README_LINES]
            parts.append(f"\n### {readme} (前 {MAX_README_LINES} 行)\n")
            parts.append("\n".join(lines))
            break

    # 目录结构
    try:
        result = subprocess.run(
            ["find", ".", "-maxdepth", str(MAX_TREE_DEPTH),
             "-not", "-path", "./.git/*",
             "-not", "-path", "./node_modules/*",
             "-not", "-path", "./.venv/*",
             "-not", "-path", "./venv/*",
             "-not", "-path", "./__pycache__/*",
             "-not", "-path", "./dist/*",
             "-not", "-path", "./.next/*",
             "-not", "-name", ".DS_Store"],
            cwd=project_dir, capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            parts.append("\n### 目录结构\n")
            parts.append(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    # requirements.txt / package.json
    for dep_file in ["requirements.txt", "package.json", "pyproject.toml", "Cargo.toml"]:
        dep_path = project_dir / dep_file
        if dep_path.exists():
            content = dep_path.read_text(errors="ignore")
            # package.json 只取前 30 行
            lines = content.splitlines()[:30]
            parts.append(f"\n### {dep_file}\n")
            parts.append("\n".join(lines))

    # 入口文件检测
    entry_files = []
    for pattern in ["app.py", "main.py", "cli.py", "index.py", "run.py",
                     "web_app.py", "server.py", "__main__.py",
                     "index.js", "index.ts", "main.rs"]:
        found = list(project_dir.rglob(pattern))
        entry_files.extend(f.relative_to(project_dir) for f in found
                          if ".venv" not in str(f) and "node_modules" not in str(f))
    if entry_files:
        parts.append("\n### 入口文件\n")
        parts.append("\n".join(str(f) for f in entry_files[:10]))

    return "\n".join(parts)


def clean_output(text: str) -> str:
    """清理 claude 输出中的包裹文字"""
    lines = text.strip().splitlines()

    # 找到第一个 # 标题行
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i
            break

    # 去掉末尾的 ``` 和 --- 和多余文字
    end = len(lines)
    while end > start:
        stripped = lines[end - 1].strip()
        if stripped in ("```", "---", "") or stripped.startswith("需要") or stripped.startswith("如果"):
            end -= 1
        else:
            break

    # 去掉开头的 ```markdown
    if start > 0 and lines[start - 1].strip().startswith("```"):
        pass  # 已经跳过了

    return "\n".join(lines[start:end])


def generate_claude_md(project_dir: Path, model: str = "sonnet") -> str | None:
    """调用 claude CLI 生成 CLAUDE.md 内容"""
    context = collect_context(project_dir)
    prompt = STYLE_PROMPT.format(context=context)

    system_prompt = (
        "你是一个文件生成器。你只输出纯 markdown 内容，不输出任何解释、确认、"
        "代码块包裹或对话文字。第一行必须是 # 标题。"
    )
    try:
        result = subprocess.run(
            ["claude", "-p", "--model", model,
             "--system-prompt", system_prompt,
             prompt],
            capture_output=True, text=True, timeout=120,
            cwd=project_dir
        )
        if result.returncode == 0 and result.stdout.strip():
            return clean_output(result.stdout)
        else:
            print(f"  ✗ claude 调用失败: {result.stderr.strip()[:200]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"  ✗ 超时 (120s)")
        return None
    except FileNotFoundError:
        print("  ✗ claude CLI 未找到")
        return None


def git_commit(project_dir: Path, force: bool = False):
    """git add + commit CLAUDE.md"""
    # 检查是否是 git 仓库
    if not (project_dir / ".git").exists():
        return False

    action = "update" if force else "add"
    subprocess.run(["git", "add", "CLAUDE.md"], cwd=project_dir,
                   capture_output=True)
    result = subprocess.run(
        ["git", "commit", "-m", f"{action} CLAUDE.md"],
        cwd=project_dir, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  ✓ committed")
        return True
    else:
        # 可能没有变更
        if "nothing to commit" in result.stdout + result.stderr:
            print(f"  - 无变更，跳过 commit")
        else:
            print(f"  ✗ commit 失败: {result.stderr.strip()[:100]}")
        return False


def get_projects(names: list[str] | None = None) -> list[Path]:
    """获取待处理的项目列表"""
    if names:
        projects = []
        for name in names:
            p = DEV_DIR / name
            if p.is_dir():
                projects.append(p)
            else:
                print(f"⚠ 跳过不存在的项目: {name}")
        return projects

    # 扫描 ~/Dev 下所有含 .git 的目录
    projects = sorted(
        p for p in DEV_DIR.iterdir()
        if p.is_dir() and (p / ".git").exists()
    )
    return projects


def main():
    parser = argparse.ArgumentParser(description="批量生成 CLAUDE.md")
    parser.add_argument("projects", nargs="*", help="项目名（默认扫描 ~/Dev）")
    parser.add_argument("--force", action="store_true", help="覆盖已有 CLAUDE.md")
    parser.add_argument("--no-commit", action="store_true", help="只生成不 commit")
    parser.add_argument("--dry-run", action="store_true", help="只列出待处理项目")
    parser.add_argument("--model", default="sonnet", help="claude 模型 (默认 sonnet)")
    args = parser.parse_args()

    projects = get_projects(args.projects or None)

    # 过滤已有 CLAUDE.md 的项目
    if not args.force:
        to_process = [p for p in projects if not (p / "CLAUDE.md").exists()]
        skipped = len(projects) - len(to_process)
        if skipped:
            print(f"跳过 {skipped} 个已有 CLAUDE.md 的项目（用 --force 覆盖）")
    else:
        to_process = projects

    if not to_process:
        print("没有需要处理的项目")
        return

    if args.dry_run:
        print(f"待处理 {len(to_process)} 个项目:")
        for p in to_process:
            print(f"  {p.name}")
        return

    print(f"开始处理 {len(to_process)} 个项目...\n")
    success, failed = 0, 0

    for i, project in enumerate(to_process, 1):
        print(f"[{i}/{len(to_process)}] {project.name}")
        content = generate_claude_md(project, model=args.model)
        if content:
            (project / "CLAUDE.md").write_text(content + "\n")
            print(f"  ✓ 生成 CLAUDE.md ({len(content.splitlines())} 行)")
            if not args.no_commit:
                git_commit(project, force=args.force)
            success += 1
        else:
            failed += 1
        print()

    print(f"完成: {success} 成功, {failed} 失败")


if __name__ == "__main__":
    main()
