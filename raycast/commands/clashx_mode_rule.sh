#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_rule
# @raycast.description Switch ClashX to rule-based proxy mode
# @raycast.mode fullOutput
# @raycast.icon 📋
# @raycast.packageName Network
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "network/clashx_mode_rule.sh" "$@"
