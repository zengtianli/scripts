#!/bin/bash
# 发送测试页
# Canon iR C3322L

PRINTER_NAME="Canon_iR_C3322L"

echo "发送测试页到 $PRINTER_NAME ..."

result=$(echo "Canon iR C3322L 测试页 - $(date '+%Y-%m-%d %H:%M:%S')" | lp -d "$PRINTER_NAME" 2>&1)

if [ $? -eq 0 ]; then
    echo "✓ $result"
    sleep 3
    status=$(lpstat -p "$PRINTER_NAME" 2>&1)
    echo "  打印机状态: $status"
else
    echo "✗ 发送失败: $result"
    echo "  运行 scripts/diagnose.sh 排查问题"
fi
