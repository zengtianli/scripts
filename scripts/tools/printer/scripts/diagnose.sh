#!/bin/bash
# 打印机一键诊断脚本
# Canon iR C3322L @ 192.168.32.173

PRINTER_IP="192.168.32.173"
PRINTER_NAME="Canon_iR_C3322L"

echo "=============================="
echo " Canon iR C3322L 诊断"
echo "=============================="

# 1. 网络连通性
echo ""
echo "[1/5] 网络连通性 (ping)"
if /sbin/ping -c 2 -t 2 "$PRINTER_IP" &>/dev/null; then
    echo "  ✓ ping 通了"
else
    echo "  ✗ ping 不通 — 检查网络连接或打印机是否开机"
    exit 1
fi

# 2. 端口检测
echo ""
echo "[2/5] 端口检测"
for port in 9100 631 80; do
    if nc -z -w 3 "$PRINTER_IP" "$port" 2>/dev/null; then
        echo "  ✓ 端口 $port 开放"
    else
        echo "  ✗ 端口 $port 关闭"
    fi
done

# 3. 代理检测
echo ""
echo "[3/5] 代理环境变量"
proxy_vars=$(env | grep -i proxy 2>/dev/null)
if [ -n "$proxy_vars" ]; then
    echo "  ⚠ 检测到代理设置:"
    echo "$proxy_vars" | sed 's/^/    /'
    echo "  → 如果代理没运行，会导致 ipp:// 协议失败"
    echo "  → 当前使用 socket:// 协议可绕过此问题"
else
    echo "  ✓ 无代理设置"
fi

# 4. CUPS 打印机状态
echo ""
echo "[4/5] CUPS 打印机状态"
if lpstat -p "$PRINTER_NAME" &>/dev/null; then
    status=$(lpstat -p "$PRINTER_NAME" 2>&1)
    echo "  $status"
    uri=$(lpstat -v "$PRINTER_NAME" 2>&1)
    echo "  $uri"
else
    echo "  ✗ 打印机 $PRINTER_NAME 未在 CUPS 中注册"
    echo "  → 运行 scripts/fix.sh 重新添加"
fi

# 5. 打印队列
echo ""
echo "[5/5] 打印队列"
queue=$(lpq -P "$PRINTER_NAME" 2>&1)
echo "  $queue"

echo ""
echo "=============================="
echo " 诊断完成"
echo "=============================="
