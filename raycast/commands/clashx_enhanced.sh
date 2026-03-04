#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_enhanced
# @raycast.description Enhanced ClashX proxy management and configuration
# @raycast.mode fullOutput
# @raycast.icon ⚙️
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "network/clashx_enhanced.sh" "$@"
