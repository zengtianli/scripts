#!/bin/bash

# 每日工作报告提醒
# 每天 18:00 提醒查看工作报告
# 由 launchd 在 17:50 触发（提前 10 分钟创建提醒）

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REMINDER_SCRIPT="$SCRIPT_DIR/create_reminder.sh"

# 计算提醒时间（今天 18:00）
REMINDER_TIME=$(date '+%Y-%m-%d 18:00')

# 创建提醒
"$REMINDER_SCRIPT" "查看今日工作报告" "$REMINDER_TIME" "paper work" "$@"
