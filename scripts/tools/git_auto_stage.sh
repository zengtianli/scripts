#!/bin/bash
# git_auto_stage.sh — PostToolUse Hook：文件改动后自动 git add
# 用法：由 CC Hook 自动调用，检查文件是否在 Git 仓库中，是则 git add
# 不做 commit/push，攒着等 git_push_all.sh 批量推

f="$CLAUDE_TOOL_INPUT_FILE_PATH"
[ -z "$f" ] && exit 0
[ ! -f "$f" ] && exit 0

# 检查文件是否在 Git 仓库中
repo_root=$(cd "$(dirname "$f")" && git rev-parse --show-toplevel 2>/dev/null)
[ -z "$repo_root" ] && exit 0

# git add（静默，不影响 CC 输出）
cd "$repo_root" && git add "$f" 2>/dev/null

exit 0
