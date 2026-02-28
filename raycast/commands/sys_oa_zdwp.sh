#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title 水利公司 OA
# @raycast.mode silent
# @raycast.icon 🌊
# @raycast.packageName System
# @raycast.description 启动水利公司 OA 管理面板
source "$(dirname "$0")/../lib/run_python.sh" && run_shell "sys_oa_zdwp.sh" "$@"
