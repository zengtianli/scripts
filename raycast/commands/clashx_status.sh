#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_status
# @raycast.mode fullOutput
# @raycast.icon 🌐
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "clashx_status.sh" "$@"
