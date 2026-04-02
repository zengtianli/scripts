#!/usr/bin/env python3
"""cc_sessions.py - Claude Code 会话管理统一工具。

合并了原 session_indexer.py（索引）和 export_cc_sessions.py（导出）的功能。

子命令:
    index  [--summarize]                                    → 扫描会话文件，生成 session_index.json
    export [--date-from DATE] [--date-to DATE] [--project]  → 导出会话为 Markdown

示例:
    python3 cc_sessions.py index                           # 增量索引所有会话
    python3 cc_sessions.py index --summarize               # 索引并用 LLM 生成摘要
    python3 cc_sessions.py export                          # 导出最近 7 天
    python3 cc_sessions.py export --date-from 2026-03-01   # 从指定日期开始
    python3 cc_sessions.py export --project Dev-scripts    # 筛选特定项目
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── 路径设置（公共库） ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# ── 常量 ────────────────────────────────────────────────────────────────────
PROJECTS_DIR = Path.home() / ".claude" / "projects"
OUTPUT_DIR = Path.home() / "docs" / "sessions" / "exports"
DEFAULT_DAYS = 7
LOCAL_TZ = timezone(timedelta(hours=8))  # 中国标准时间 UTC+8

# 会话质量阈值（index 子命令用）
MIN_MESSAGE_COUNT = 6  # 至少 6 条消息
MIN_FILE_SIZE_KB = 10  # 至少 10KB


# ════════════════════════════════════════════════════════════════════════════
#  共享工具函数
# ════════════════════════════════════════════════════════════════════════════


def find_session_files(projects_dir: str | Path) -> list[Path]:
    """查找 projects_dir/PROJECT/*.jsonl（depth-1），跳过 subagent 子目录。"""
    results = []
    projects_path = Path(projects_dir)
    if not projects_path.is_dir():
        print(f"Error: {projects_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    for project_dir in sorted(projects_path.iterdir()):
        if not project_dir.is_dir():
            continue
        for jsonl_file in project_dir.glob("*.jsonl"):
            if jsonl_file.is_file():
                results.append(jsonl_file)

    return results


def extract_timestamp(obj: dict) -> str | None:
    """从 JSONL 对象中提取时间戳。"""
    ts = obj.get("timestamp")
    if ts:
        return ts

    msg = obj.get("message", {})
    if isinstance(msg, dict):
        ts = msg.get("timestamp") or msg.get("createdAt")
        if ts:
            return ts

    return None


def dir_name_to_project(dir_name: str) -> str:
    """将目录名转换为可读的项目名。

    例: '-Users-tianli-Dev-scripts' -> 'Dev/scripts'
         '-Users-tianli' -> '~ (home)'
    """
    prefix = "-Users-tianli"
    if dir_name == prefix:
        return "~ (home)"
    if dir_name.startswith(prefix + "-"):
        remainder = dir_name[len(prefix) + 1 :]
        remainder = remainder.rstrip("-")
        remainder = re.sub(r"-{2,}", "-", remainder)
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


# ════════════════════════════════════════════════════════════════════════════
#  index 子命令相关
# ════════════════════════════════════════════════════════════════════════════


def count_lines_fast(filepath: str) -> int:
    """Count lines in a file without reading entire content into memory."""
    count = 0
    with open(filepath, "rb") as f:
        buf = f.read(1024 * 1024)
        while buf:
            count += buf.count(b"\n")
            buf = f.read(1024 * 1024)
    return count


def read_head_tail(filepath: str, head: int = 10, tail: int = 5) -> list[str]:
    """Read first `head` and last `tail` lines of a file efficiently."""
    lines_head = []
    lines_tail = []

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i < head:
                lines_head.append(line)
            lines_tail.append(line)
            if len(lines_tail) > tail:
                lines_tail.pop(0)

    return lines_head + lines_tail


def extract_user_title(content) -> str:
    """Extract a title from the first user message content.

    Handles both string content and list-of-dicts content structures.
    Strips teammate-message XML wrappers if present.
    Truncates to ~50 characters.
    """
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "tool_result":
                    continue
                if item.get("type") == "text":
                    text = item.get("text", "")
                    break
        if not text:
            return ""

    if not text:
        return ""

    skip_prefixes = (
        "<local-command-caveat>",
        "<command-name>",
        "<system-reminder>",
    )
    text_stripped = text.strip()
    if any(text_stripped.startswith(p) for p in skip_prefixes):
        return ""

    text = re.sub(r"<[^>]+>", "", text).strip()

    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            text = line
            break

    text = text.strip("*_`#> ")

    if len(text) > 50:
        text = text[:47] + "..."

    return text


def parse_session(filepath: str) -> dict | None:
    """Parse a single JSONL session file and return its metadata.

    Only reads first 10 + last 5 lines for performance.
    """
    try:
        file_size = os.path.getsize(filepath)
        message_count = count_lines_fast(filepath)
        lines = read_head_tail(filepath, head=10, tail=5)
    except OSError:
        return None

    session_id = Path(filepath).stem
    project = Path(filepath).parent.name

    first_timestamp = None
    last_timestamp = None
    title = ""
    cwd = ""
    found_first_user = False

    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        if not cwd and obj.get("cwd"):
            cwd = obj["cwd"]

        ts = extract_timestamp(obj)

        if ts:
            if first_timestamp is None:
                first_timestamp = ts
            last_timestamp = ts

        line_type = obj.get("type", "")
        if not found_first_user and line_type == "user":
            msg = obj.get("message", {})
            if isinstance(msg, dict) and msg.get("role") == "user":
                content = msg.get("content", "")
                if content:
                    extracted = extract_user_title(content)
                    if extracted:
                        title = extracted
                        found_first_user = True

    if not first_timestamp:
        return None

    duration_minutes = 0
    if first_timestamp and last_timestamp and first_timestamp != last_timestamp:
        try:
            t1 = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
            t2 = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            delta = (t2 - t1).total_seconds()
            duration_minutes = max(0, round(delta / 60))
        except (ValueError, TypeError):
            duration_minutes = 0

    return {
        "session_id": session_id,
        "project": project,
        "start_time": first_timestamp,
        "duration_minutes": duration_minutes,
        "message_count": message_count,
        "title": title,
        "file_size_kb": round(file_size / 1024),
        "cwd": cwd,
    }


def is_trivial(entry: dict) -> bool:
    """判断会话是否为测试/垃圾会话。"""
    msgs = entry.get("message_count", 0)
    size = entry.get("file_size_kb", 0)
    return msgs < MIN_MESSAGE_COUNT and size < MIN_FILE_SIZE_KB


def read_session_content(filepath: str, max_chars: int = 8000) -> str:
    """读取会话文件，提取用户和助手的文本消息，限制总字符数。"""
    texts = []
    total = 0
    try:
        with open(filepath, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue

                msg = obj.get("message", {})
                if not isinstance(msg, dict):
                    continue

                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    continue

                content = msg.get("content", "")
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            text += item.get("text", "") + "\n"

                if not text.strip():
                    continue

                text = re.sub(r"<[^>]+>", "", text).strip()
                if not text:
                    continue

                prefix = "User: " if role == "user" else "Assistant: "
                chunk = prefix + text[:500] + "\n"
                if total + len(chunk) > max_chars:
                    break
                texts.append(chunk)
                total += len(chunk)
    except OSError:
        pass
    return "".join(texts)


def generate_summary(content: str, title: str) -> dict | None:
    """调用智谱 API 生成会话摘要，返回 {summary, category, outcomes}。"""
    prompt = f"""分析以下 Claude Code 会话内容，用中文返回 JSON（不要 markdown 代码块）：
{{
  "summary": "一句话总结做了什么（20-40字）",
  "category": "分类，从以下选一个：开发/配置/学习/排查/写作/整理/讨论",
  "outcomes": "关键成果或决策（20-50字，没有就写无）"
}}

会话标题：{title}
会话内容：
{content[:6000]}"""

    try:
        from tools.llm_client import chat

        text = chat(
            system="你是一个 JSON 生成器。只输出纯 JSON，不要 markdown 代码块。",
            message=prompt,
        )
        if "```" in text:
            m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if m:
                text = m.group(1)
        if not text.startswith("{"):
            m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
            if m:
                text = m.group(0)
        return json.loads(text)
    except Exception as e:
        print(f"  Summary API error: {e}", file=sys.stderr)
        return None


def load_cache(cache_path: str) -> dict:
    """Load the mtime cache from disk."""
    try:
        with open(cache_path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_cache(cache_path: str, cache: dict) -> None:
    """Save the mtime cache to disk."""
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def cmd_index(args: argparse.Namespace) -> None:
    """index 子命令：扫描会话文件，生成 session_index.json。"""
    projects_dir = str(PROJECTS_DIR)
    output_path = args.output or "session_index.json"
    do_summarize = args.summarize

    output_dir = os.path.dirname(os.path.abspath(output_path))
    cache_path = os.path.join(output_dir, ".session_cache.json")

    t0 = time.time()

    session_files = find_session_files(projects_dir)

    cache = load_cache(cache_path)

    # Load existing index for cached entries
    existing_index = {}
    try:
        with open(output_path, encoding="utf-8") as f:
            for entry in json.load(f):
                key = os.path.join(
                    projects_dir, entry["project"], entry["session_id"] + ".jsonl"
                )
                existing_index[key] = entry
    except (OSError, json.JSONDecodeError, ValueError, KeyError):
        pass

    results = []
    new_count = 0
    cached_count = 0

    for fp in session_files:
        filepath = str(fp)
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            continue

        mtime_str = str(mtime)

        if filepath in cache and cache[filepath] == mtime_str:
            if filepath in existing_index:
                results.append(existing_index[filepath])
                cached_count += 1
                continue

        entry = parse_session(filepath)
        if entry:
            results.append(entry)
            cache[filepath] = mtime_str
            new_count += 1

    # Mark trivial sessions
    trivial_count = 0
    for entry in results:
        if is_trivial(entry):
            entry["trivial"] = True
            trivial_count += 1

    # Generate summaries for non-trivial sessions (incremental)
    summary_count = 0
    if do_summarize:
        need_summary = [
            e for e in results if not e.get("trivial") and not e.get("summary")
        ]
        if need_summary:
            print(
                f"Generating summaries for {len(need_summary)} sessions...",
                file=sys.stderr,
            )
        for entry in need_summary:
            sid = entry["session_id"]
            proj = entry["project"]
            filepath = os.path.join(projects_dir, proj, sid + ".jsonl")
            if not os.path.exists(filepath):
                continue

            content = read_session_content(filepath)
            if not content:
                continue

            result = generate_summary(content, entry.get("title", ""))
            if result:
                entry["summary"] = result.get("summary", "")
                entry["category"] = result.get("category", "")
                entry["outcomes"] = result.get("outcomes", "")
                summary_count += 1
                print(
                    f"  [{summary_count}/{len(need_summary)}] {sid[:8]}... → {entry['summary'][:40]}",
                    file=sys.stderr,
                )
                time.sleep(0.5)

    # Sort by start_time descending
    results.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    save_cache(cache_path, cache)

    elapsed = time.time() - t0
    total = new_count + cached_count
    valid = total - trivial_count
    print(
        f"Indexed {total} sessions ({new_count} new, {cached_count} cached, "
        f"{trivial_count} trivial, {valid} valid) in {elapsed:.1f}s",
        file=sys.stderr,
    )
    if summary_count:
        print(f"Generated {summary_count} new summaries", file=sys.stderr)


# ════════════════════════════════════════════════════════════════════════════
#  export 子命令相关
# ════════════════════════════════════════════════════════════════════════════


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
            desc = _summarize_tool_call(tool_name, tool_input)
            parts.append(f"[Tool: {tool_name}] {desc}")

    return "\n\n".join(parts)


def _summarize_tool_call(tool_name: str, tool_input: dict) -> str:
    """为工具调用生成简要描述。"""
    if not isinstance(tool_input, dict):
        return ""

    if tool_name in ("Read", "ReadFile", "Write", "WriteFile", "Edit", "EditFile"):
        return tool_input.get("file_path", "")
    elif tool_name in ("Bash", "BashCommand"):
        cmd = tool_input.get("command", "")
        desc = tool_input.get("description", "")
        if desc:
            return desc
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
        if content.startswith("<local-command-caveat>"):
            return True
        if content.startswith("<command-name>"):
            return True
        if content.startswith("<local-command-stdout>"):
            return True
    return False


def parse_jsonl_file(filepath: Path) -> list[dict]:
    """解析 JSONL 文件，返回消息列表（export 子命令用，完整解析）。"""
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

            if entry_type not in ("user", "assistant"):
                continue

            if entry.get("isSidechain", False):
                continue

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

    first_ts = ""
    if messages and messages[0].get("timestamp"):
        try:
            dt = datetime.fromisoformat(
                messages[0]["timestamp"].replace("Z", "+00:00")
            ).astimezone(LOCAL_TZ)
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
                dt = datetime.fromisoformat(
                    msg["timestamp"].replace("Z", "+00:00")
                ).astimezone(LOCAL_TZ)
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
        print(f"错误：项目目录不存在: {PROJECTS_DIR}", file=sys.stderr)
        sys.exit(1)

    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue

        project_name = dir_name_to_project(project_dir.name)

        if project_filter:
            filter_lower = project_filter.lower()
            if (
                filter_lower not in project_name.lower()
                and filter_lower not in project_dir.name.lower()
            ):
                continue

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

    by_project: dict[str, list[dict]] = {}
    for info in exported_files:
        proj = info["project"]
        by_project.setdefault(proj, []).append(info)

    for proj in sorted(by_project.keys()):
        lines.append(f"## {proj}")
        lines.append("")
        lines.append("| 文件 | 消息数 | 大小 | 时间 |")
        lines.append("|------|--------|------|------|")
        for info in sorted(
            by_project[proj], key=lambda x: x["mtime"], reverse=True
        ):
            md_name = info["md_filename"]
            msg_count = info["message_count"]
            size = info["size"]
            mtime = info["mtime"]
            lines.append(
                f"| [{md_name}]({md_name}) | {msg_count} | {size} | {mtime} |"
            )
        lines.append("")

    content = "\n".join(lines)
    index_path.write_text(content, encoding="utf-8")
    return index_path


def cmd_export(args: argparse.Namespace) -> None:
    """export 子命令：将会话导出为 Markdown。"""
    # 解析日期
    if args.date_from:
        date_from = datetime.strptime(args.date_from, "%Y-%m-%d")
    else:
        date_from = datetime.now() - timedelta(days=DEFAULT_DAYS)
    date_from = date_from.replace(hour=0, minute=0, second=0, microsecond=0)

    if args.date_to:
        date_to = datetime.strptime(args.date_to, "%Y-%m-%d")
        date_to = date_to.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        date_to = None

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

        stat = filepath.stat()
        mtime_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y%m%d_%H%M")
        safe_project = (
            project_name.replace("/", "_")
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
        )
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
                "mtime": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M"
                ),
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


# ════════════════════════════════════════════════════════════════════════════
#  CLI 入口
# ════════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Claude Code 会话管理工具（索引 + 导出）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  %(prog)s index                                # 增量索引所有会话
  %(prog)s index --summarize                    # 索引并生成 LLM 摘要
  %(prog)s export                               # 导出最近 7 天的会话
  %(prog)s export --date-from 2026-03-01        # 从指定日期开始导出
  %(prog)s export --project scripts             # 只导出特定项目""",
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # index 子命令
    p_index = subparsers.add_parser(
        "index", help="扫描会话文件，生成 session_index.json"
    )
    p_index.add_argument(
        "--summarize",
        action="store_true",
        help="用 LLM 为非琐碎会话生成摘要",
    )
    p_index.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="输出 JSON 路径，默认: session_index.json",
    )

    # export 子命令
    p_export = subparsers.add_parser(
        "export", help="将会话导出为 Markdown 格式"
    )
    p_export.add_argument(
        "--date-from",
        type=str,
        default=None,
        help="开始日期 (YYYY-MM-DD)，默认为 7 天前",
    )
    p_export.add_argument(
        "--date-to",
        type=str,
        default=None,
        help="结束日期 (YYYY-MM-DD)，默认为今天",
    )
    p_export.add_argument(
        "--project",
        type=str,
        default=None,
        help="筛选特定项目（模糊匹配目录名或项目名）",
    )
    p_export.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=f"输出目录，默认: {OUTPUT_DIR}",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "index":
        cmd_index(args)
    elif args.command == "export":
        cmd_export(args)


if __name__ == "__main__":
    main()
