#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_status
# @raycast.description Display current ClashX proxy status and configuration
# @raycast.mode fullOutput
# @raycast.icon 🌐
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "network/clashx_status.sh" "$@"
