#!/bin/bash
# Raycast Script
# @raycast.schemaVersion 1
# @raycast.title folder_paste
# @raycast.mode fullOutput
# @raycast.icon 📋
# @raycast.packageName Custom

# 引入通用函数库
source "$(dirname "${BASH_SOURCE[0]}")/common_functions.sh"

# 记录使用统计
log_script_usage "folders/folder_paste.sh" "folders"

# 调用独立的粘贴脚本
exec "$PASTE_TO_FINDER_SCRIPT" 
