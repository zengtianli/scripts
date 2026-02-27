#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 水利公司 OA
# @raycast.mode silent
# @raycast.packageName System

# Optional parameters:
# @raycast.icon 🌊
# @raycast.description 启动水利公司 OA 管理面板

OA_DIR="$HOME/Downloads/zdwp/.oa"
PORT=3001

# 检查端口是否已在运行
if lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1; then
    open "http://localhost:$PORT"
    exit 0
fi

cd "$OA_DIR" || exit 1
nohup pnpm dev --port $PORT >/dev/null 2>&1 &
sleep 2
open "http://localhost:$PORT"
