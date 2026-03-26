#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_global
# @raycast.mode fullOutput
# @raycast.icon 🌍
# @raycast.packageName Network

# Documentation:
# @raycast.description Set ClashX Pro to Global mode

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../lib/clashx.sh"

log_script_usage "clashx_mode_global.sh" "network"
clashx_set_mode "global"
