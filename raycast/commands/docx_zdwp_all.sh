#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title docx-zdwp-all
# @raycast.mode fullOutput
# @raycast.icon ✨
# @raycast.packageName Document Processing
# @raycast.description One-click ZDWP document standardization (6 steps)
source "$(dirname "$0")/../lib/run_python.sh" && run_python "document/docx_zdwp_all.py" "$@"
