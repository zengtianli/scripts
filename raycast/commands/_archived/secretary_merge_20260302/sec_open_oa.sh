#!/bin/bash

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.packageName 秘书系统
# @raycast.title 打开 OA
# @raycast.description 启动并打开智能秘书 OA 系统
# @raycast.icon 🏢
# @raycast.mode silent

OA_DIR="$HOME/cursor-shared/.oa"
OA_URL="http://localhost:3000"
PORT=3000
MAX_WAIT=10

# 检查端口是否被占用
check_port() {
    lsof -i :$PORT -sTCP:LISTEN >/dev/null 2>&1
}

# 等待服务启动
wait_for_service() {
    local count=0
    while [ $count -lt $MAX_WAIT ]; do
        if check_port; then
            return 0
        fi
        sleep 1
        count=$((count + 1))
    done
    return 1
}

# 检查 OA 是否已运行
if check_port; then
    echo "OA 已在运行，直接打开浏览器"
    open "$OA_URL"
    exit 0
fi

# 检查目录是否存在
if [ ! -d "$OA_DIR" ]; then
    echo "错误：OA 目录不存在 ($OA_DIR)"
    exit 1
fi

# 启动 OA 服务
echo "启动 OA 服务..."
cd "$OA_DIR" || exit 1

# 后台启动服务，输出重定向到日志文件
nohup pnpm dev:oa > /tmp/oa.log 2>&1 &
OA_PID=$!

# 等待服务启动
if wait_for_service; then
    echo "OA 服务启动成功 (PID: $OA_PID)"
    open "$OA_URL"
else
    echo "错误：OA 服务启动超时，请检查日志 /tmp/oa.log"
    exit 1
fi
