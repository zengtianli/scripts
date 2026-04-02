#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title CC Sessions Export
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Secretary
# @raycast.description 导出 Claude Code 对话历史为 Markdown 格式（最近 7 天）
# @raycast.argument1 { "type": "text", "placeholder": "天数 (默认 7)", "optional": true }

source "$(dirname "$0")/../lib/run_python.sh" && run_python "tools/cc_sessions.py" export --date-from "$(date -v-${1:-7}d +%Y-%m-%d)"
