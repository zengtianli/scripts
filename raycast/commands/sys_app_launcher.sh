#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title sys-app-launcher
# @raycast.mode fullOutput
# @raycast.icon 🚀
# @raycast.packageName System
source "$(dirname "$0")/../lib/run_python.sh" && run_python "system/sys_app_launcher.py" "$@"
