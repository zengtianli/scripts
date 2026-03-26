#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_enhanced
# @raycast.mode fullOutput
# @raycast.icon ⚙️
# @raycast.packageName Network

# Documentation:
# @raycast.description Toggle ClashX Pro Enhanced Mode (TUN)

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../lib/clashx.sh"

log_script_usage "clashx_enhanced.sh" "network"
clashx_toggle_enhanced
