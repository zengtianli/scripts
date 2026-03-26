#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title file-run
# @raycast.mode fullOutput
# @raycast.icon 🚀
# @raycast.packageName Files
# @raycast.description Run selected shell or python scripts
# @raycast.argument1 { "type": "dropdown", "placeholder": "Mode", "data": [{"title": "Single", "value": "single"}, {"title": "Parallel", "value": "parallel"}] }
source "$(dirname "$0")/../lib/run_python.sh" && run_python "file/file_run.py" "$@"
