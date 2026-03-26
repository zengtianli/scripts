#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_status
# @raycast.mode fullOutput
# @raycast.icon 🌐
# @raycast.packageName Network

# Documentation:
# @raycast.description Show ClashX Pro status

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../lib/clashx.sh"

log_script_usage "clashx_status.sh" "network"
clashx_show_status
