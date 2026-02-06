#!/bin/bash
# Raycast Script
# @raycast.schemaVersion 1
# @raycast.title folder_paste
# @raycast.mode fullOutput
# @raycast.icon 📋
# @raycast.packageName Custom

# 引入通用函数库
source "$(dirname "${BASH_SOURCE[0]}")/../lib/common.sh"

# 记录使用统计
log_script_usage "folders/folder_paste.sh" "folders"

# 粘贴剪贴板中的文件到 Finder 当前目录
osascript -e 'tell application "System Events" to keystroke "v" using command down'

show_success "已执行粘贴操作"
