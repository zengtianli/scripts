#!/bin/bash
# ============================================================
# ClashX Pro 公共函数库
# 位置：execute/raycast/_lib/clashx.sh
# 更新：2026-01-14
# ============================================================
# 使用说明: source "$(dirname "$0")/_lib/clashx.sh"
# ============================================================

# ===== 辅助函数 =====

# 获取 ClashX Pro 的 API 端口（动态）
get_api_port() {
    lsof -i -P -n 2>/dev/null | grep "ClashX" | grep "LISTEN" | grep "127.0.0.1" | awk '{print $9}' | cut -d: -f2 | head -1
}

# 检查 ClashX Pro 是否运行
check_clashx_running() {
    if ! pgrep -f "ClashX Pro" > /dev/null 2>&1; then
        show_error "ClashX Pro 未运行"
        exit 1
    fi
}

# 获取当前系统代理状态
get_proxy_status() {
    local enabled=$(networksetup -getwebproxy Wi-Fi 2>/dev/null | grep "^Enabled:" | awk '{print $2}')
    if [ "$enabled" = "Yes" ]; then
        echo "on"
    else
        echo "off"
    fi
}

# 获取当前代理模式
get_proxy_mode() {
    local port=$(get_api_port)
    if [ -z "$port" ]; then
        echo "unknown"
        return
    fi
    curl --noproxy '*' -s "http://127.0.0.1:$port/configs" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('mode','unknown'))" 2>/dev/null || echo "unknown"
}

# 获取 Enhanced Mode 状态
get_enhanced_status() {
    local status=$(defaults read com.west2online.ClashXPro autoEnableTun 2>/dev/null)
    if [ "$status" = "1" ]; then
        echo "on"
    else
        echo "off"
    fi
}

# ===== 操作函数 =====

# 显示当前状态
clashx_show_status() {
    check_clashx_running
    
    echo "🌐 ClashX Pro 状态"
    echo "─────────────────────"
    
    local proxy_status=$(get_proxy_status)
    local proxy_mode=$(get_proxy_mode)
    local enhanced=$(get_enhanced_status)
    
    if [ "$proxy_status" = "on" ]; then
        echo "系统代理: ✅ 开启"
    else
        echo "系统代理: ⭕ 关闭"
    fi
    
    echo "代理模式: 📋 $proxy_mode"
    
    if [ "$enhanced" = "on" ]; then
        echo "增强模式: ✅ 开启"
    else
        echo "增强模式: ⭕ 关闭"
    fi
}

# 切换系统代理
clashx_toggle_proxy() {
    check_clashx_running
    
    osascript -e 'tell application "ClashX Pro" to toggleProxy' 2>/dev/null
    
    sleep 0.5
    local new_status=$(get_proxy_status)
    
    if [ "$new_status" = "on" ]; then
        show_success "系统代理已开启"
    else
        show_success "系统代理已关闭"
    fi
}

# 设置代理模式
clashx_set_mode() {
    check_clashx_running
    
    local mode="$1"
    
    if [[ ! "$mode" =~ ^(rule|direct|global)$ ]]; then
        show_error "无效模式: $mode (可选: rule, direct, global)"
        exit 1
    fi
    
    osascript -e "tell application \"ClashX Pro\" to proxyMode \"$mode\"" 2>/dev/null
    
    sleep 0.5
    local new_mode=$(get_proxy_mode)
    show_success "代理模式: $new_mode"
}

# 切换增强模式 (GUI 自动化)
clashx_toggle_enhanced() {
    # GUI 自动化点击菜单栏
    osascript 2>/dev/null <<'EOF'
tell application "System Events" to tell process "ClashX Pro"
    click menu bar item 1 of menu bar 2
    delay 0.05
    click menu item "Enhanced Mode" of menu 1 of menu bar item 1 of menu bar 2
end tell
EOF
    
    if [ $? -eq 0 ]; then
        [ "$(defaults read com.west2online.ClashXPro autoEnableTun 2>/dev/null)" = "1" ] && echo "✅ Enhanced: ON" || echo "✅ Enhanced: OFF"
    else
        echo "❌ 需要辅助功能权限"
    fi
}
