#!/bin/bash
# 打印机修复脚本 — 删除旧配置，用 socket 协议重新添加
# Canon iR C3322L @ 192.168.32.173

PRINTER_IP="192.168.32.173"
PRINTER_NAME="Canon_iR_C3322L"
PPD_BACKUP="/tmp/canon_c3322l.ppd"
PPD_SYSTEM="/private/etc/cups/ppd/_192_168_32_173.ppd"

echo "=============================="
echo " Canon iR C3322L 修复"
echo "=============================="

# 1. 备份 PPD
echo ""
echo "[1/4] 备份驱动文件"
if [ -f "$PPD_SYSTEM" ]; then
    cp "$PPD_SYSTEM" "$PPD_BACKUP"
    echo "  ✓ PPD 已备份到 $PPD_BACKUP"
elif [ -f "$PPD_BACKUP" ]; then
    echo "  ✓ 使用已有备份 $PPD_BACKUP"
else
    echo "  ✗ 找不到 PPD 文件，尝试无驱动模式"
    PPD_BACKUP=""
fi

# 2. 取消所有任务并删除旧打印机
echo ""
echo "[2/4] 清理旧配置"
cancel -a 2>/dev/null
# 删除可能存在的各种名称
for name in "$PRINTER_NAME" "_192_168_32_173" "_192_168_32_173_2"; do
    if lpstat -p "$name" &>/dev/null; then
        lpadmin -x "$name" 2>/dev/null
        echo "  ✓ 已删除 $name"
    fi
done

# 3. 用 socket 协议重新添加
echo ""
echo "[3/4] 添加打印机 (socket://$PRINTER_IP:9100)"
if [ -n "$PPD_BACKUP" ]; then
    lpadmin -p "$PRINTER_NAME" \
        -v "socket://$PRINTER_IP:9100" \
        -P "$PPD_BACKUP" \
        -D "Canon iR C3322L" \
        -L "Office" \
        -E 2>&1
else
    lpadmin -p "$PRINTER_NAME" \
        -v "socket://$PRINTER_IP:9100" \
        -m everywhere \
        -D "Canon iR C3322L" \
        -L "Office" \
        -E 2>&1
fi

# 4. 设为默认
echo ""
echo "[4/4] 设为默认打印机"
lpoptions -d "$PRINTER_NAME" >/dev/null 2>&1

# 验证
echo ""
if lpstat -p "$PRINTER_NAME" &>/dev/null; then
    echo "✓ 修复完成！"
    lpstat -v "$PRINTER_NAME"
    echo ""
    echo "运行 scripts/test-print.sh 验证打印"
else
    echo "✗ 修复失败，请检查错误信息"
fi
