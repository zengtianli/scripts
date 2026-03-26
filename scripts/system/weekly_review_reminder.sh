#!/bin/bash

# 每周工作总结提醒
# 每周五 17:00 提醒查看工作总结
# 由 launchd 在 16:50 触发（提前 10 分钟创建提醒）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMINDER_SCRIPT="$SCRIPT_DIR/create_reminder.sh"

# 检查是否为周五（1=周一, 5=周五）
WEEKDAY=$(date +%u)

if [ "$WEEKDAY" -eq 5 ]; then
    # 计算提醒时间（今天 17:00）
    REMINDER_TIME=$(date '+%Y-%m-%d 17:00')

    # 创建提醒
    "$REMINDER_SCRIPT" "查看本周工作总结" "$REMINDER_TIME" "paper work" "$@"
else
    echo "ℹ️  今天不是周五，跳过提醒创建"
fi
