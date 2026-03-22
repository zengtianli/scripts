#!/bin/bash
# auto_git_sync.sh - 自动同步所有核心 repo 到 GitHub

REPOS=(
  "$HOME/Dev/scripts"
  "$HOME/docs"
  "$HOME/.claude"
  "$HOME/Work/zdwp"
  "$HOME/Learn"
)

for repo in "${REPOS[@]}"; do
  if [ ! -d "$repo/.git" ]; then
    continue
  fi
  cd "$repo"
  if [ -n "$(git status --porcelain)" ]; then
    git add -A
    git commit -m "auto: sync $(date '+%Y-%m-%d %H:%M')"
    git push origin HEAD 2>&1 | tail -1
    echo "✅ $repo synced"
  else
    echo "⏭️  $repo no changes"
  fi
done

echo "done"
