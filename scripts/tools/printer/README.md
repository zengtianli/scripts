# Canon iR C3322L 打印机管理

办公室 Canon iR C3322L 网络打印机的诊断、修复和管理脚本。

## 背景

macOS 通过网络连接 Canon iR C3322L（IP: 192.168.32.173）。
系统配置了代理 `all_proxy=127.0.0.1:7890`，代理未运行时会导致 IPP 协议通信失败。
解决方案：使用 `socket://` 协议直连端口 9100，绕过代理。

## 脚本

| 脚本 | 用途 |
|------|------|
| `scripts/diagnose.sh` | 一键诊断打印机连接状态 |
| `scripts/fix.sh` | 删除旧配置，用 socket 协议重新添加打印机 |
| `scripts/test-print.sh` | 发送测试页 |

## 快速使用

```bash
# 打印机出问题了？先诊断
bash scripts/diagnose.sh

# 确认是代理/协议问题后，一键修复
bash scripts/fix.sh

# 验证修复结果
bash scripts/test-print.sh
```

## 2026-02-27 故障记录

**现象**：早上能打印，之后无法打印，CUPS 持续报 "Unable to get printer status"
**根因**：`all_proxy=127.0.0.1:7890` 代理服务未运行，`ipp://` 协议走 HTTP 被代理拦截
**修复**：将协议从 `ipp://192.168.32.173/` 改为 `socket://192.168.32.173:9100`
