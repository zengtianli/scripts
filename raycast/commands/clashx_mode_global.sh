#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_global
# @raycast.description Switch ClashX to global proxy mode
# @raycast.mode fullOutput
# @raycast.icon 🌍
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "network/clashx_mode_global.sh" "$@"
