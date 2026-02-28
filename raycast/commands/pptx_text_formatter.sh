#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title pptx-text
# @raycast.mode fullOutput
# @raycast.icon 📽️
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "document/pptx_text_formatter.py" "$@"
