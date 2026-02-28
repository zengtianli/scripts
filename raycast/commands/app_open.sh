#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title app-open
# @raycast.mode silent
# @raycast.icon 🚀
# @raycast.packageName Apps
# @raycast.description Open selected folder in specified app
# @raycast.argument1 { "type": "dropdown", "placeholder": "App", "data": [{"title": "Cursor", "value": "cursor"}, {"title": "Terminal", "value": "terminal"}, {"title": "Windsurf", "value": "windsurf"}, {"title": "Nvim", "value": "nvim"}] }
source "$(dirname "$0")/../lib/run_python.sh" && run_python "app_open.py" "$@"
