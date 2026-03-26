#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_direct
# @raycast.description Switch ClashX to direct connection mode
# @raycast.mode fullOutput
# @raycast.icon ⚡
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "network/clashx_mode_direct.sh" "$@"
