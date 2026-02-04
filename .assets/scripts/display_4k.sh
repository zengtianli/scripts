#!/bin/bash

# Raycast parameters
# @raycast.schemaVersion 1
# @raycast.title display_4k
# @raycast.mode fullOutput
# @raycast.icon 🖥️
# @raycast.packageName Display

# Documentation:
# @raycast.description Set external displays to 4K (3840x2160)

# 获取外接显示器 ID（排除内置屏幕）
get_external_ids() {
    displayplacer list 2>/dev/null | grep -B5 "Type: 27 inch" | grep "Persistent screen id:" | awk '{print $4}'
}

# 设置分辨率
IDS=$(get_external_ids)

if [ -z "$IDS" ]; then
    echo "❌ 未检测到外接显示器"
    exit 1
fi

CMD="displayplacer"
for id in $IDS; do
    CMD="$CMD \"id:$id res:3840x2160 hz:60 color_depth:8 scaling:off\""
done

eval $CMD 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 外接显示器已切换到 4K"
else
    echo "❌ 切换失败"
fi
