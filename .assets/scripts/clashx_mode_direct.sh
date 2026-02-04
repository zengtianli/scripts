#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_direct
# @raycast.mode fullOutput
# @raycast.icon ⚡
# @raycast.packageName Network

# Documentation:
# @raycast.description Set ClashX Pro to Direct mode

source "$(dirname "$0")/_lib/common.sh"
source "$(dirname "$0")/_lib/clashx.sh"

log_script_usage "clashx_mode_direct.sh" "network"
clashx_set_mode "direct"
