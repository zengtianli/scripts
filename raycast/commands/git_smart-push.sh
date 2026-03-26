#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Smart Push All Repos
# @raycast.mode fullOutput

# Optional parameters:
# @raycast.icon 🚀
# @raycast.packageName Git
# @raycast.description AI commit message + push all GitHub repos

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
PYTHON=$(which python3)

"$PYTHON" "$REPO_ROOT/scripts/tools/git_smart_push.py"
