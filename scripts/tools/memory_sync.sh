#!/bin/bash
# memory_sync.sh — PostToolUse Hook：memory 文件修改后自动同步到 docs/memory/
f="$CLAUDE_TOOL_INPUT_FILE_PATH"
[ -z "$f" ] && exit 0

# 只处理 memory 目录下的文件
case "$f" in
  $HOME/.claude/projects/-Users-tianli/memory/*)
    cp "$f" "$HOME/docs/memory/" 2>/dev/null
    ;;
esac
exit 0
