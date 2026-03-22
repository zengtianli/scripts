#!/usr/bin/env python3
"""cc_chat_server.py — CC 产物管理中心 Chat API Backend

A Chat API backend for the CC Artifact Management Center.
Receives chat messages from a browser-embedded chat widget and uses
Claude API with tool-use to answer questions and perform file operations.

Usage:
    python3 cc_chat_server.py

Environment variables:
    MMKG_BASE_URL   - Claude API base URL
    MMKG_AUTH_TOKEN  - Claude API auth token
    DOCS_ROOT            - Knowledge base root (default: /var/www/docs/)
    CC_ROOT              - CC artifacts root (default: /var/www/claude-config/)
    CHAT_PORT            - Server port (default: 7892)

Test:
    curl -X POST http://127.0.0.1:7892/api/chat \
      -H 'Content-Type: application/json' \
      -d '{"message":"hello"}'
"""

import glob
import json
import os
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PORT = int(os.environ.get("CHAT_PORT", "7892"))
HOST = "127.0.0.1"

DOCS_ROOT = os.environ.get("DOCS_ROOT", "/var/www/docs/")
CC_ROOT = os.environ.get("CC_ROOT", "/var/www/claude-config/")

BASE_URL = os.environ.get("MMKG_BASE_URL", "").rstrip("/")
AUTH_TOKEN = os.environ.get("MMKG_AUTH_TOKEN", "")

MODEL = "claude-haiku-4-5-20251001"
MAX_TOOL_ROUNDS = 10

SYSTEM_PROMPT = f"""\
You are a CC (Claude Code) artifact management assistant.
You help users manage their knowledge base and CC configuration files.

Available directories:
- DOCS_ROOT ({DOCS_ROOT}): Knowledge base — sessions, memory, knowledge files
- CC_ROOT ({CC_ROOT}): CC artifacts — rules, standards, skills, memory files

Capabilities:
- Read, write, delete, search, list files
- Merge multiple memory/knowledge files (preserve ALL specific details, dates,
  decisions — never compress into vague bullet points)
- Git commit and push changes

Rules:
- Before destructive operations (delete, overwrite), explain what you will do
  and why, so the user can confirm.
- The .claude/ directory is the authoritative source for CC artifacts.
- Always respond in the same language the user uses.
- When merging files, keep every concrete detail: dates, file paths, decisions,
  rationale. Do NOT summarize or compress.
"""

# ---------------------------------------------------------------------------
# Tool definitions (Claude API format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file. Path must be within DOCS_ROOT or CC_ROOT.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Absolute path or relative path within allowed roots",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file. Path must be within DOCS_ROOT or CC_ROOT. Parent directories will be created if needed.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to write to",
                },
                "content": {
                    "type": "string",
                    "description": "Content to write",
                },
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "delete_file",
        "description": "Delete a file. Path must be within DOCS_ROOT or CC_ROOT.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path to delete",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "list_files",
        "description": "List directory contents. Optionally filter by glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path to list",
                },
                "pattern": {
                    "type": "string",
                    "description": "Optional glob pattern (e.g. '*.md', '**/*.md')",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "merge_files",
        "description": "Merge multiple files into one. Preserves all specific details, dates, and decisions — does not compress.",
        "input_schema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths to merge",
                },
                "output_path": {
                    "type": "string",
                    "description": "Output file path for merged content",
                },
            },
            "required": ["paths", "output_path"],
        },
    },
    {
        "name": "git_commit_push",
        "description": "Stage all changes (git add -A), commit with message, and push to remote.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Commit message",
                },
                "repo_dir": {
                    "type": "string",
                    "description": "Repository directory path",
                },
            },
            "required": ["message", "repo_dir"],
        },
    },
    {
        "name": "search_files",
        "description": "Search file contents using grep. Returns matching lines with file paths.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Search pattern (grep regex)",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (defaults to DOCS_ROOT)",
                },
            },
            "required": ["pattern"],
        },
    },
]

# ---------------------------------------------------------------------------
# Path security
# ---------------------------------------------------------------------------


def _resolve(path_str: str) -> str:
    """Resolve a path string to an absolute, symlink-resolved path."""
    return str(Path(path_str).resolve())


def _allowed_roots() -> list[str]:
    """Return resolved allowed root directories."""
    roots = []
    for root in (DOCS_ROOT, CC_ROOT):
        resolved = _resolve(root)
        # Ensure trailing slash for prefix matching
        if not resolved.endswith("/"):
            resolved += "/"
        roots.append(resolved)
    return roots


def validate_path(path_str: str) -> str:
    """Validate that a path is within allowed roots. Returns resolved path.

    Raises ValueError if path is outside allowed roots.
    """
    resolved = _resolve(path_str)
    roots = _allowed_roots()
    for root in roots:
        # Allow the root directory itself or anything inside it
        if resolved == root.rstrip("/") or resolved.startswith(root):
            return resolved
    raise ValueError(
        f"Path '{path_str}' is outside allowed directories. "
        f"Allowed: {DOCS_ROOT}, {CC_ROOT}"
    )


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def tool_read_file(path: str) -> str:
    safe_path = validate_path(path)
    if not os.path.isfile(safe_path):
        return f"Error: File not found: {safe_path}"
    try:
        content = Path(safe_path).read_text(encoding="utf-8")
        if len(content) > 50000:
            return content[:50000] + f"\n\n[Truncated — file is {len(content)} bytes]"
        return content
    except Exception as e:
        return f"Error reading file: {e}"


def tool_write_file(path: str, content: str) -> str:
    safe_path = validate_path(path)
    try:
        os.makedirs(os.path.dirname(safe_path), exist_ok=True)
        Path(safe_path).write_text(content, encoding="utf-8")
        return f"OK: Written {len(content)} bytes to {safe_path}"
    except Exception as e:
        return f"Error writing file: {e}"


def tool_delete_file(path: str) -> str:
    safe_path = validate_path(path)
    if not os.path.exists(safe_path):
        return f"Error: File not found: {safe_path}"
    try:
        os.remove(safe_path)
        return f"OK: Deleted {safe_path}"
    except Exception as e:
        return f"Error deleting file: {e}"


def tool_list_files(path: str, pattern: str | None = None) -> str:
    safe_path = validate_path(path)
    if not os.path.isdir(safe_path):
        return f"Error: Not a directory: {safe_path}"
    try:
        if pattern:
            full_pattern = os.path.join(safe_path, pattern)
            matches = sorted(glob.glob(full_pattern, recursive=True))
            entries = [os.path.relpath(m, safe_path) for m in matches]
        else:
            entries = sorted(os.listdir(safe_path))
            # Annotate directories with trailing /
            annotated = []
            for e in entries:
                full = os.path.join(safe_path, e)
                annotated.append(e + "/" if os.path.isdir(full) else e)
            entries = annotated
        if not entries:
            return f"(empty directory: {safe_path})"
        return "\n".join(entries)
    except Exception as e:
        return f"Error listing directory: {e}"


def tool_merge_files(paths: list[str], output_path: str) -> str:
    safe_output = validate_path(output_path)
    parts = []
    for p in paths:
        safe_p = validate_path(p)
        if not os.path.isfile(safe_p):
            return f"Error: File not found: {safe_p}"
        try:
            content = Path(safe_p).read_text(encoding="utf-8")
            parts.append(f"# === Source: {safe_p} ===\n\n{content}")
        except Exception as e:
            return f"Error reading {safe_p}: {e}"
    merged = "\n\n".join(parts)
    try:
        os.makedirs(os.path.dirname(safe_output), exist_ok=True)
        Path(safe_output).write_text(merged, encoding="utf-8")
        return (
            f"OK: Merged {len(paths)} files into {safe_output} "
            f"({len(merged)} bytes)"
        )
    except Exception as e:
        return f"Error writing merged file: {e}"


def tool_git_commit_push(message: str, repo_dir: str) -> str:
    safe_dir = validate_path(repo_dir)
    if not os.path.isdir(os.path.join(safe_dir, ".git")):
        return f"Error: Not a git repository: {safe_dir}"
    try:
        results = []
        for cmd in [
            ["git", "add", "-A"],
            ["git", "commit", "-m", message],
            ["git", "push"],
        ]:
            proc = subprocess.run(
                cmd,
                cwd=safe_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            results.append(f"$ {' '.join(cmd)}\n{proc.stdout}{proc.stderr}")
            if proc.returncode != 0 and cmd[1] != "push":
                # Allow push failures to still report, but stop on add/commit failures
                return "\n".join(results) + f"\n(exit code {proc.returncode})"
        return "\n".join(results)
    except subprocess.TimeoutExpired:
        return "Error: Git command timed out (30s)"
    except Exception as e:
        return f"Error running git: {e}"


def tool_search_files(pattern: str, path: str | None = None) -> str:
    search_dir = path or DOCS_ROOT
    safe_dir = validate_path(search_dir)
    if not os.path.isdir(safe_dir):
        return f"Error: Not a directory: {safe_dir}"
    try:
        proc = subprocess.run(
            ["grep", "-r", "-n", "-i", "--include=*.md", "--include=*.txt",
             "--include=*.py", "--include=*.json", "--include=*.yaml",
             "--include=*.yml", pattern, safe_dir],
            capture_output=True,
            text=True,
            timeout=15,
        )
        output = proc.stdout.strip()
        if not output:
            return f"No matches found for '{pattern}' in {safe_dir}"
        # Truncate if too long
        lines = output.split("\n")
        if len(lines) > 100:
            output = "\n".join(lines[:100]) + f"\n\n[Truncated — {len(lines)} total matches]"
        return output
    except subprocess.TimeoutExpired:
        return "Error: Search timed out (15s)"
    except Exception as e:
        return f"Error searching: {e}"


# Tool dispatch table
TOOL_DISPATCH = {
    "read_file": lambda inp: tool_read_file(inp["path"]),
    "write_file": lambda inp: tool_write_file(inp["path"], inp["content"]),
    "delete_file": lambda inp: tool_delete_file(inp["path"]),
    "list_files": lambda inp: tool_list_files(inp["path"], inp.get("pattern")),
    "merge_files": lambda inp: tool_merge_files(inp["paths"], inp["output_path"]),
    "git_commit_push": lambda inp: tool_git_commit_push(inp["message"], inp["repo_dir"]),
    "search_files": lambda inp: tool_search_files(inp["pattern"], inp.get("path")),
}

# ---------------------------------------------------------------------------
# Claude API caller
# ---------------------------------------------------------------------------


def call_claude(messages: list[dict], tools: list[dict], system: str) -> dict:
    """Call Claude API with tool-use support. Returns the response body dict.

    Raises HTTPError or other exceptions on failure.
    Includes 429 exponential backoff retry (1s, 2s, 4s, max 3 retries).
    """
    import time

    url = f"{BASE_URL}/v1/messages"
    payload = {
        "model": MODEL,
        "max_tokens": 4096,
        "system": system,
        "tools": tools,
        "messages": messages,
    }
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "x-api-key": AUTH_TOKEN,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01",
        "user-agent": "curl/8.0",
    }

    max_retries = 3
    for attempt in range(max_retries + 1):
        req = Request(url, data=data, headers=headers, method="POST")
        try:
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError as e:
            if e.code == 429 and attempt < max_retries:
                wait = 2 ** attempt
                log(f"Rate limited, retrying in {wait}s...")
                time.sleep(wait)
                continue
            # Read error body for debugging
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            log(f"Claude API error {e.code}: {error_body[:500]}")
            raise


# ---------------------------------------------------------------------------
# Tool-use loop
# ---------------------------------------------------------------------------


def run_chat(user_message: str, history: list[dict] | None = None) -> dict:
    """Run the full tool-use loop. Returns {"response": str, "tool_calls": int}."""
    messages = []

    # Add conversation history if provided
    if history:
        messages.extend(history)

    # Add current user message
    messages.append({"role": "user", "content": user_message})

    total_tool_calls = 0

    for round_num in range(MAX_TOOL_ROUNDS):
        response = call_claude(messages, TOOLS, SYSTEM_PROMPT)
        content_blocks = response.get("content", [])
        stop_reason = response.get("stop_reason", "")

        # Extract tool_use blocks
        tool_uses = [b for b in content_blocks if b["type"] == "tool_use"]

        if not tool_uses:
            # No tool calls — extract text response and return
            text_parts = [b["text"] for b in content_blocks if b["type"] == "text"]
            final_text = "\n".join(text_parts) if text_parts else ""
            return {"response": final_text, "tool_calls": total_tool_calls}

        # There are tool calls — execute them
        # First, append the assistant's response to messages
        messages.append({"role": "assistant", "content": content_blocks})

        # Execute each tool and build tool_result blocks
        tool_results = []
        for tool_use in tool_uses:
            tool_name = tool_use["name"]
            tool_input = tool_use["input"]
            tool_id = tool_use["id"]
            total_tool_calls += 1

            log(f"Tool call [{total_tool_calls}]: {tool_name}({json.dumps(tool_input, ensure_ascii=False)[:200]})")

            handler = TOOL_DISPATCH.get(tool_name)
            if handler:
                try:
                    result = handler(tool_input)
                except ValueError as e:
                    result = f"Security error: {e}"
                except Exception as e:
                    result = f"Error executing {tool_name}: {e}"
            else:
                result = f"Unknown tool: {tool_name}"

            log(f"  -> Result: {result[:200]}")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result,
            })

        # Append tool results as user message
        messages.append({"role": "user", "content": tool_results})

    # Exhausted max rounds
    return {
        "response": "I've reached the maximum number of tool-use rounds (10). "
                     "Please try a simpler request.",
        "tool_calls": total_tool_calls,
    }


# ---------------------------------------------------------------------------
# HTTP Server
# ---------------------------------------------------------------------------


def log(msg: str):
    """Log to stderr."""
    print(f"[cc_chat] {msg}", file=sys.stderr, flush=True)


class ChatHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the chat API."""

    def log_message(self, format, *args):
        """Override default logging to use stderr with prefix."""
        log(f"{self.address_string()} - {format % args}")

    def _send_json(self, data: dict, status: int = 200):
        """Send a JSON response."""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        """Read and parse JSON request body."""
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/api/health":
            self._send_json({"status": "ok"})
        else:
            self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        """Handle POST requests."""
        if self.path != "/api/chat":
            self._send_json({"error": "Not found"}, 404)
            return

        try:
            body = self._read_body()
        except (json.JSONDecodeError, Exception) as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, 400)
            return

        message = body.get("message", "").strip()
        if not message:
            self._send_json({"error": "Missing 'message' field"}, 400)
            return

        history = body.get("history", [])
        log(f"Chat request: {message[:100]}{'...' if len(message) > 100 else ''}")

        try:
            result = run_chat(message, history)
            self._send_json(result)
        except HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass
            log(f"Claude API error: {e.code} - {error_body[:300]}")
            self._send_json(
                {"error": f"Claude API error: {e.code}", "detail": error_body[:500]},
                502,
            )
        except Exception as e:
            log(f"Internal error: {e}")
            self._send_json({"error": f"Internal server error: {e}"}, 500)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    if not BASE_URL:
        print("Error: MMKG_BASE_URL not set", file=sys.stderr)
        sys.exit(1)
    if not AUTH_TOKEN:
        print("Error: MMKG_AUTH_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    log(f"DOCS_ROOT: {DOCS_ROOT}")
    log(f"CC_ROOT:   {CC_ROOT}")
    log(f"Model:     {MODEL}")
    log(f"Starting server on {HOST}:{PORT}")

    server = HTTPServer((HOST, PORT), ChatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log("Shutting down...")
        server.server_close()


if __name__ == "__main__":
    main()
