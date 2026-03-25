#!/usr/bin/env python3
"""Index Claude Code JSONL session files and produce session_index.json.

Usage:
    python3 session_indexer.py <projects_dir> [output.json]

Scans <projects_dir>/PROJECT/*.jsonl (depth-1 only, skips subagent files),
extracts metadata from each session, and writes a JSON index sorted by
start_time descending.

Supports incremental indexing via mtime caching to avoid re-parsing
unchanged files.
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

# 会话质量阈值
MIN_MESSAGE_COUNT = 6  # 至少 6 条消息
MIN_FILE_SIZE_KB = 10  # 至少 10KB


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
    """Read first `head` and last `tail` lines of a file efficiently.

    Returns a combined list of lines (head lines first, then tail lines).
    Duplicates are possible if the file has fewer than head+tail lines.
    """
    lines_head = []
    lines_tail = []

    with open(filepath, encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i < head:
                lines_head.append(line)
            # Keep a rolling buffer for the tail
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
                # Skip tool_result items - they are not user messages
                if item.get("type") == "tool_result":
                    continue
                if item.get("type") == "text":
                    text = item.get("text", "")
                    break
        # If only tool_results found, this is not a real first user message
        if not text:
            return ""

    if not text:
        return ""

    # Skip system-like messages wrapped in XML
    skip_prefixes = (
        "<local-command-caveat>",
        "<command-name>",
        "<system-reminder>",
    )
    text_stripped = text.strip()
    if any(text_stripped.startswith(p) for p in skip_prefixes):
        return ""

    # Strip XML-like wrappers (teammate-message, etc.)
    text = re.sub(r"<[^>]+>", "", text).strip()

    # Clean up: take first meaningful line
    for line in text.split("\n"):
        line = line.strip()
        if line and not line.startswith("#") and not line.startswith("---"):
            text = line
            break

    # Remove markdown formatting
    text = text.strip("*_`#> ")

    # Truncate
    if len(text) > 50:
        text = text[:47] + "..."

    return text


def extract_timestamp(obj: dict) -> str | None:
    """Extract timestamp from a parsed JSONL object."""
    # Direct timestamp field
    ts = obj.get("timestamp")
    if ts:
        return ts

    # Inside message
    msg = obj.get("message", {})
    if isinstance(msg, dict):
        ts = msg.get("timestamp") or msg.get("createdAt")
        if ts:
            return ts

    return None


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

        # Extract cwd from first available line
        if not cwd and obj.get("cwd"):
            cwd = obj["cwd"]

        # Get timestamp
        ts = extract_timestamp(obj)

        # Track first and last timestamps
        if ts:
            if first_timestamp is None:
                first_timestamp = ts
            last_timestamp = ts

        # Extract title from first user message
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

    # Calculate duration
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

                # 清理 XML 标签
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
    """调用 API 生成会话摘要，返回 {summary, category, outcomes}。"""
    base_url = os.environ.get("MMKG_BASE_URL", "")
    auth_token = os.environ.get("MMKG_AUTH_TOKEN", "")
    if not base_url or not auth_token:
        return None

    prompt = f"""分析以下 Claude Code 会话内容，用中文返回 JSON（不要 markdown 代码块）：
{{
  "summary": "一句话总结做了什么（20-40字）",
  "category": "分类，从以下选一个：开发/配置/学习/排查/写作/整理/讨论",
  "outcomes": "关键成果或决策（20-50字，没有就写无）"
}}

会话标题：{title}
会话内容：
{content[:6000]}"""

    payload = json.dumps(
        {
            "model": "claude-sonnet-4-6",
            "max_tokens": 200,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    url = base_url.rstrip("/") + "/v1/messages"
    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": auth_token,
            "anthropic-version": "2023-06-01",
            "User-Agent": "curl/8.7.1",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            text = ""
            for block in result.get("content", []):
                if block.get("type") == "text":
                    text += block.get("text", "")
            # 从返回文本中提取 JSON 对象
            text = text.strip()
            # 去掉可能的 markdown 代码块包裹
            if "```" in text:
                m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
                if m:
                    text = m.group(1)
            # 如果不是以 { 开头，尝试提取 JSON 对象
            if not text.startswith("{"):
                m = re.search(r"\{[^{}]*\}", text, re.DOTALL)
                if m:
                    text = m.group(0)
            return json.loads(text)
    except (urllib.error.URLError, json.JSONDecodeError, Exception) as e:
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


def find_session_files(projects_dir: str) -> list[str]:
    """Find all depth-1 JSONL files under projects_dir.

    Returns paths matching: projects_dir/PROJECT/*.jsonl
    Skips subagent files in deeper directories.
    """
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
                results.append(str(jsonl_file))

    return results


def main():
    # Parse args
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]

    if len(args) < 1:
        print(
            "Usage: python3 session_indexer.py <projects_dir> [output.json] [--summarize]",
            file=sys.stderr,
        )
        sys.exit(1)

    projects_dir = args[0]
    output_path = args[1] if len(args) > 1 else "session_index.json"
    do_summarize = "--summarize" in flags

    # Cache lives next to the output file
    output_dir = os.path.dirname(os.path.abspath(output_path))
    cache_path = os.path.join(output_dir, ".session_cache.json")

    t0 = time.time()

    # Find all session files
    session_files = find_session_files(projects_dir)

    # Load existing cache and index
    cache = load_cache(cache_path)

    # Load existing index for cached entries
    existing_index = {}
    try:
        with open(output_path, encoding="utf-8") as f:
            for entry in json.load(f):
                key = os.path.join(projects_dir, entry["project"], entry["session_id"] + ".jsonl")
                existing_index[key] = entry
    except (OSError, json.JSONDecodeError, ValueError, KeyError):
        pass

    results = []
    new_count = 0
    cached_count = 0

    for filepath in session_files:
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            continue

        mtime_str = str(mtime)

        # Check if file is unchanged since last index
        if filepath in cache and cache[filepath] == mtime_str:
            # Use cached result if available
            if filepath in existing_index:
                results.append(existing_index[filepath])
                cached_count += 1
                continue

        # Parse the session file
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
        need_summary = [e for e in results if not e.get("trivial") and not e.get("summary")]
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
                # 不要太快，避免 rate limit
                time.sleep(0.5)

    # Sort by start_time descending (newest first)
    results.sort(key=lambda x: x.get("start_time", ""), reverse=True)

    # Write output
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # Save cache
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


if __name__ == "__main__":
    main()
