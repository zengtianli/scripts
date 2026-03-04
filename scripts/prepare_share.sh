#!/bin/bash
# prepare_share.sh - 准备项目用于分享
#
# 用法:
#   ./prepare_share.sh                    # 使用 rsync（推荐）
#   ./prepare_share.sh --dereference      # 使用 Python 脚本

set -e

PROJECT_DIR="$1"
METHOD="${2:---rsync}"

if [[ -z "$PROJECT_DIR" ]]; then
    echo "用法: $0 <项目目录> [--rsync|--dereference]"
    echo ""
    echo "示例:"
    echo "  $0 ~/useful_scripts              # 使用 rsync（推荐）"
    echo "  $0 ~/useful_scripts --dereference # 使用 Python 脚本"
    exit 1
fi

PROJECT_DIR=$(cd "$PROJECT_DIR" && pwd)
PROJECT_NAME=$(basename "$PROJECT_DIR")
SHARE_DIR="/tmp/${PROJECT_NAME}_share"
ARCHIVE="/tmp/${PROJECT_NAME}_$(date +%Y%m%d_%H%M%S).tar.gz"

echo "📦 准备分享项目: $PROJECT_NAME"
echo "   源目录: $PROJECT_DIR"
echo "   临时目录: $SHARE_DIR"
echo ""

# 清理旧的临时目录
if [[ -d "$SHARE_DIR" ]]; then
    echo "🗑️  清理旧的临时目录..."
    rm -rf "$SHARE_DIR"
fi

if [[ "$METHOD" == "--rsync" ]]; then
    echo "📋 方法: rsync -L（自动解引用符号链接）"
    echo ""

    # 使用 rsync -L 自动解引用符号链接
    rsync -avL --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
        "$PROJECT_DIR/" "$SHARE_DIR/"

elif [[ "$METHOD" == "--dereference" ]]; then
    echo "📋 方法: Python 脚本（手动解引用）"
    echo ""

    # 先复制整个项目
    cp -R "$PROJECT_DIR" "$SHARE_DIR"

    # 运行 dereference 脚本
    python3 "$(dirname "$0")/dereference_links.py" "$SHARE_DIR"

else
    echo "❌ 未知方法: $METHOD"
    exit 1
fi

echo ""
echo "📦 创建压缩包..."
tar -czf "$ARCHIVE" -C "$(dirname "$SHARE_DIR")" "$(basename "$SHARE_DIR")"

echo ""
echo "✅ 完成！"
echo "   压缩包: $ARCHIVE"
echo "   大小: $(du -h "$ARCHIVE" | cut -f1)"
echo ""
echo "🧹 清理临时目录..."
rm -rf "$SHARE_DIR"

echo ""
echo "🎉 项目已准备好分享！"
echo "   文件: $ARCHIVE"
