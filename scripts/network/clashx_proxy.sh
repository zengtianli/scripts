#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_proxy
# @raycast.mode fullOutput
# @raycast.icon 🔄
# @raycast.packageName Network

# Documentation:
# @raycast.description Toggle ClashX Pro system proxy

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../lib/clashx.sh"

log_script_usage "clashx_proxy.sh" "network"
clashx_toggle_proxy
