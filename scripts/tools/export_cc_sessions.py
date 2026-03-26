#!/usr/bin/env python3
"""
export_cc_sessions.py - 将 Claude Code JSONL 对话历史导出为可读的 Markdown 格式

扫描 ~/.claude/projects/ 下的 .jsonl 文件，按日期筛选后转换为 Markdown。

用法:
    python3 export_cc_sessions.py                          # 导出最近 7 天
    python3 export_cc_sessions.py --date-from 2026-03-01   # 从指定日期开始
    python3 export_cc_sessions.py --date-to 2026-03-10     # 到指定日期结束
    python3 export_cc_sessions.py --project Dev-scripts    # 筛选特定项目
"""

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── 常量 ───────────────────────────────────────────────────────────────────
PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUTPUT_DIR = Path.home() / "docs" / "sessions" / "exports"
DEFAULT_DAYS = 7
LOCAL_TZ = timezone(timedelta(hours=8))  # 中国标准时间 UTC+8


# ── 工具函数 ───────────────────────────────────────────────────────────────
def dir_name_to_project(dir_name: str) -> str:
    """将目录名转换为可读的项目名。

    例: '-Users-tianli-Dev-scripts' -> 'Dev/scripts'
         '-Users-tianli' -> '~ (home)'
         '-Users-tianli-Work-zdwp---------------------------' -> 'Work/zdwp'
    """
    import re

    # 去掉前缀 -Users-tianli
    prefix = "-Users-tianli"
    if dir_name == prefix:
        return "~ (home)"
    if dir_name.startswith(prefix + "-"):
        remainder = dir_name[len(prefix) + 1 :]
        # 清理末尾多余的连字符（中文路径编码残留）
        remainder = remainder.rstrip("-")
        # 清理中间连续的多个连字符为单个
        remainder = re.sub(r"-{2,}", "-", remainder)
        # 将 - 转换为 /
        return remainder.replace("-", "/")
    return dir_name


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小为人类可读格式。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def extract_text_from_content(content) -> str:
    """从 message.content 提取文本内容。

    content 可能是:
    - str: 直接返回
    - list: 遍历提取 text 类型的内容，tool_use 只记录名称
    """
    if isinstance(content, str):
        return content.strip()

    if not isinstance(content, list):
        return ""

    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        item_type = item.get("type", "")

        if item_type == "text":
            text = item.get("text", "").strip()
            if text:
                parts.append(text)

        elif item_type == "tool_use":
            tool_name = item.get("name", "unknown")
            tool_input = item.get("input", {})
            # 根据工具类型生成简要描述
            desc = _summarize_tool_call(tool_name, tool_input)
            parts.append(f"[Tool: {tool_name}] {desc}")

        # tool_result 类型跳过（通常在 user 消息中，是工具返回值）

    return "\n\n".join(parts)


def _summarize_tool_call(tool_name: str, tool_input: dict) -> str:
    """为工具调用生成简要描述。"""
    if not isinstance(tool_input, dict):
        return ""

    # 根据常见工具类型提取关键信息
    if tool_name in ("Read", "ReadFile") or tool_name in ("Write", "WriteFile") or tool_name in ("Edit", "EditFile"):
        return tool_input.get("file_path", "")
    elif tool_name in ("Bash", "BashCommand"):
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        if desc:
            return desc
        # 截断过长的命令
        return cmd[:120] + "..." if len(cmd) > 120 else cmd
    elif tool_name in ("Grep", "Search"):
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", "")
        return f'pattern="{pattern}" path={path}'
    elif tool_name in ("Glob", "GlobSearch"):
        return tool_input.get("pattern", "")
    elif tool_name in ("WebFetch",):
        return tool_input.get("url", "")
    elif tool_name in ("WebSearch",) or tool_name in ("ToolSearch",):
        return tool_input.get("query", "")
    elif tool_name in ("TaskUpdate",):
        status = tool_input.get("status", "")
        return f"status={status}"
    else:
        # 通用：列出输入的 key
        keys = list(tool_input.keys())
        if keys:
            return f"keys: {', '.join(keys[:5])}"
        return ""


def is_meta_or_system_message(entry: dict) -> bool:
    """判断是否为元数据/系统消息，应该跳过。"""
    if entry.get("isMeta", False):
        return True
    msg = entry.get("message", {})
    if not isinstance(msg, dict):
        return True
    content = msg.get("content", "")
    if isinstance(content, str):
        # 跳过纯系统指令消息
        if content.startswith("<local-command-caveat>"):
            return True
        if content.startswith("<command-name>"):
            return True
        if content.startswith("<local-command-stdout>"):
            return True
    return False


def parse_jsonl_file(filepath: Path) -> list[dict]:
    """解析 JSONL 文件，返回消息列表。"""
    messages = []
    with open(filepath, encoding="utf-8") as f:
        for _line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type", "")

            # 只处理 user 和 assistant 消息
            if entry_type not in ("user", "assistant"):
                continue

            # 跳过侧链消息
            if entry.get("isSidechain", False):
                continue

            # 跳过元数据/系统消息
            if is_meta_or_system_message(entry):
                continue

            msg = entry.get("message", {})
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", entry_type)
            content = msg.get("content", "")
            timestamp = entry.get("timestamp", "")

            text = extract_text_from_content(content)
            if not text:
                continue

            messages.append(
                {
                    "role": role,
                    "text": text,
                    "timestamp": timestamp,
                }
            )

    return messages


def generate_markdown(filepath: Path, project_name: str, messages: list[dict]) -> str:
    """将解析后的消息列表转换为 Markdown 字符串。"""
    stat = filepath.stat()
    file_size = format_file_size(stat.st_size)
    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    # 从第一条消息提取日期
    first_ts = ""
    if messages and messages[0].get("timestamp"):
        try:
            dt = datetime.fromisoformat(messages[0]["timestamp"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
            first_ts = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            first_ts = ""

    session_date = first_ts or mtime.split(" ")[0]
    session_id = filepath.stem

    lines = []
    lines.append(f"# 会话：{project_name} - {session_date}")
    lines.append("")
    lines.append(f"- 文件：`{filepath}`")
    lines.append(f"- 会话 ID：`{session_id}`")
    lines.append(f"- 大小：{file_size}")
    lines.append(f"- 时间：{mtime}")
    lines.append(f"- 消息数：{len(messages)}")
    lines.append("")
    lines.append("---")
    lines.append("")

    for _i, msg in enumerate(messages):
        role = msg["role"]
        text = msg["text"]
        ts = ""
        if msg.get("timestamp"):
            try:
                dt = datetime.fromisoformat(msg["timestamp"].replace("Z", "+00:00")).astimezone(LOCAL_TZ)
                ts = dt.strftime("%H:%M:%S")
            except (ValueError, AttributeError):
                ts = ""

        if role == "user":
            header = "## 用户"
        else:
            header = "## 助手"

        if ts:
            header += f" ({ts})"

        lines.append(header)
        lines.append("")
        lines.append(text)
        lines.append("")

    return "\n".join(lines)


def collect_jsonl_files(
    project_filter: str | None = None,
) -> list[tuple[Path, str]]:
    """收集所有项目目录下的 JSONL 文件（排除 subagents 子目录）。

    返回: [(filepath, project_name), ...]
    """
    results = []

    if not PROJECTS_DIR.exists():
        print(f"错误：项目目录不存在: {PROJECTS_DIR}")
        sys.exit(1)

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        project_name = dir_name_to_project(project_dir.name)

        # 按项目名筛选
        if project_filter:
            filter_lower = project_filter.lower()
            if filter_lower not in project_name.lower() and filter_lower not in project_dir.name.lower():
                continue

        # 只扫描项目目录下的直接 .jsonl 文件（排除 subagents 等子目录）
        for jsonl_file in project_dir.glob("*.jsonl"):
            if jsonl_file.is_file():
                results.append((jsonl_file, project_name))

    return results


def filter_by_date(
    files: list[tuple[Path, str]],
    date_from: datetime | None,
    date_to: datetime | None,
) -> list[tuple[Path, str]]:
    """按文件修改时间筛选。"""
    filtered = []
    for filepath, project_name in files:
        mtime = datetime.fromtimestamp(filepath.stat().st_mtime)
        if date_from and mtime < date_from:
            continue
        if date_to and mtime > date_to:
            continue
        filtered.append((filepath, project_name))
    return filtered


def generate_index(exported_files: list[dict], output_dir: Path) -> Path:
    """生成 index.md 汇总文件。"""
    index_path = output_dir / "index.md"
    lines = []
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append("# Claude Code 会话导出索引")
    lines.append("")
    lines.append(f"- 生成时间：{now}")
    lines.append(f"- 导出目录：`{output_dir}`")
    lines.append(f"- 导出数量：{len(exported_files)} 个会话")
    lines.append("")
    lines.append("---")
    lines.append("")

    # 按项目分组
    by_project: dict[str, list[dict]] = {}
    for info in exported_files:
        proj = info["project"]
        by_project.setdefault(proj, []).append(info)

    for proj in sorted(by_project.keys()):
        lines.append(f"## {proj}")
        lines.append("")
        lines.append("| 文件 | 消息数 | 大小 | 时间 |")
        lines.append("|------|--------|------|------|")
        for info in sorted(by_project[proj], key=lambda x: x["mtime"], reverse=True):
            md_name = info["md_filename"]
            msg_count = info["message_count"]
            size = info["size"]
            mtime = info["mtime"]
            lines.append(f"| [{md_name}]({md_name}) | {msg_count} | {size} | {mtime} |")
        lines.append("")

    content = "\n".join(lines)
    index_path.write_text(content, encoding="utf-8")
    return index_path


def main():
    parser = argparse.ArgumentParser(description="将 Claude Code JSONL 对话历史导出为 Markdown")
    parser.add_argument(
        "--date-from",
        type=str,
        default=None,
        help="开始日期 (YYYY-MM-DD)，默认为 7 天前",
    )
    parser.add_argument(
        "--date-to",
        type=str,
        default=None,
        help="结束日期 (YYYY-MM-DD)，默认为今天",
    )
    parser.add_argument(
        "--project",
        type=str,
        default=None,
        help="筛选特定项目（模糊匹配目录名或项目名）",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help=f"输出目录，默认: {OUTPUT_DIR}",
    )
    args = parser.parse_args()

    # 解析日期
    if args.date_from:
        date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
    else:
        date_from = datetime.now() - timedelta(days=DEFAULT_DAYS)
    # 设置为当天 00:00:00
    date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)

    if args.date_to:
        date_to = datetime.strptime(args.date_to, "%Y-%m-%d")
        # 设置为当天 23:59:59
        date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        date_to = None  # 不限制结束日期

    output_dir = Path(args.output) if args.output else OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 收集文件
    print(f"扫描目录: {PROJECTS_DIR}")
    all_files = collect_jsonl_files(project_filter=args.project)
    print(f"发现 {len(all_files)} 个 JSONL 文件")

    # 按日期筛选
    filtered_files = filter_by_date(all_files, date_from, date_to)
    date_range = f"{date_from.strftime('%Y-%m-%d')} ~ {date_to.strftime('%Y-%m-%d') if date_to else '今天'}"
    print(f"日期范围: {date_range}")
    print(f"符合条件: {len(filtered_files)} 个文件")

    if not filtered_files:
        print("没有找到符合条件的文件。")
        return

    # 处理每个文件
    exported_files = []
    for idx, (filepath, project_name) in enumerate(filtered_files, 1):
        progress = f"[{idx}/{len(filtered_files)}]"
        print(f"{progress} 处理: {project_name} / {filepath.name}")

        messages = parse_jsonl_file(filepath)
        if not messages:
            print("  -> 跳过（无有效消息）")
            continue

        markdown = generate_markdown(filepath, project_name, messages)

        # 生成输出文件名
        stat = filepath.stat()
        mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M")
        safe_project = project_name.replace("/", "_").replace(" ", "_").replace("(", "").replace(")", "")
        md_filename = f"{mtime_str}_{safe_project}_{filepath.stem[:8]}.md"
        md_path = output_dir / md_filename

        md_path.write_text(markdown, encoding="utf-8")
        print(f"  -> {md_filename} ({len(messages)} 条消息)")

        exported_files.append(
            {
                "project": project_name,
                "md_filename": md_filename,
                "message_count": len(messages),
                "size": format_file_size(stat.st_size),
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
            }
        )

    # 生成索引
    if exported_files:
        index_path = generate_index(exported_files, output_dir)
        print("\n导出完成！")
        print(f"  导出目录: {output_dir}")
        print(f"  导出文件: {len(exported_files)} 个")
        print(f"  索引文件: {index_path}")
    else:
        print("\n没有导出任何文件（所有文件均无有效消息）。")


if __name__ == "__main__":
    main()
