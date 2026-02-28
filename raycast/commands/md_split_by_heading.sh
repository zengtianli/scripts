#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title md-split
# @raycast.mode fullOutput
# @raycast.icon ✂️
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "document/md_split_by_heading.py" "$@"
