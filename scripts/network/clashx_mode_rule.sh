#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title clashx_mode_rule
# @raycast.mode fullOutput
# @raycast.icon 📋
# @raycast.packageName Network

# Documentation:
# @raycast.description Set ClashX Pro to Rule mode

source "$(dirname "$0")/../../lib/common.sh"
source "$(dirname "$0")/../../lib/clashx.sh"

log_script_usage "clashx_mode_rule.sh" "network"
clashx_set_mode "rule"
