#!/bin/bash
# git_push_all.sh — 批量 commit + push 所有有变更的 Augment 索引仓库
# 用法：手动调用或 Raycast 触发，一次性推送所有攒着的改动

REPOS=(
    "$HOME/Dev/scripts"
    "$HOME/Dev/oa-project"
    "$HOME/Learn"
    "$HOME/Personal/website"
    "$HOME/Personal/essays"
    "$HOME/Personal/resume"
    "$HOME/Work/zdwp"
    "$HOME/Work/reports"
    "$HOME/docs"
    "$HOME/.claude"
)

pushed=0
skipped=0

for repo in "${REPOS[@]}"; do
    [ ! -d "$repo/.git" ] && continue

    cd "$repo" || continue

    # 检查是否有 staged 或 unstaged 变更
    if git diff --cached --quiet 2>/dev/null && git diff --quiet 2>/dev/null; then
        ((skipped++))
        continue
    fi

    # 有变更：add all → commit → push
    git add -A 2>/dev/null
    git commit -m "auto-sync: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null
    if git push 2>/dev/null; then
        echo "✅ $(basename "$repo"): pushed"
        ((pushed++))
    else
        echo "❌ $(basename "$repo"): push failed"
    fi
done

echo ""
echo "推送完成：$pushed 个仓库有更新，$skipped 个无变更"
