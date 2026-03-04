#!/usr/bin/env python3
"""
生活秘书 - 记录生活日志
支持分类：health, social, family, hobby, todo, event
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "life_log.jsonl"

CATEGORIES = {
    "health": "健康",
    "social": "社交",
    "family": "家庭",
    "hobby": "爱好",
    "todo": "待办",
    "event": "事件"
}

PRIORITIES = ["high", "medium", "low"]


def log_entry(
    content: str,
    category: str = "event",
    tags: Optional[list] = None,
    priority: str = "medium",
    metadata: Optional[dict] = None
) -> None:
    """记录生活日志条目"""

    # 验证参数
    if category not in CATEGORIES:
        print(f"❌ 无效的分类：{category}")
        print(f"可用分类：{', '.join(CATEGORIES.keys())}")
        sys.exit(1)

    if priority not in PRIORITIES:
        print(f"❌ 无效的优先级：{priority}")
        print(f"可用优先级：{', '.join(PRIORITIES)}")
        sys.exit(1)

    # 构建日志条目
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "category": category,
        "content": content,
        "tags": tags or [],
        "priority": priority
    }

    if metadata:
        entry["metadata"] = metadata

    # 确保目录存在
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 追加到日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # 输出确认信息
    print(f"✅ 已记录生活日志")
    print(f"📁 分类：{CATEGORIES[category]}")
    print(f"📝 内容：{content}")
    if tags:
        print(f"🏷️  标签：{', '.join(tags)}")
    print(f"⭐ 优先级：{priority}")


def interactive_mode():
    """交互式输入模式"""
    print("=== 生活秘书 - 记录生活日志 ===\n")

    # 输入内容
    content = input("📝 请输入生活记录内容：").strip()
    if not content:
        print("❌ 内容不能为空")
        sys.exit(1)

    # 选择分类
    print("\n📁 请选择分类：")
    for i, (key, name) in enumerate(CATEGORIES.items(), 1):
        print(f"  {i}. {name} ({key})")

    category_input = input("请输入分类编号或名称（默认：event）：").strip()
    if not category_input:
        category = "event"
    elif category_input.isdigit():
        idx = int(category_input) - 1
        if 0 <= idx < len(CATEGORIES):
            category = list(CATEGORIES.keys())[idx]
        else:
            print("❌ 无效的编号")
            sys.exit(1)
    elif category_input in CATEGORIES:
        category = category_input
    else:
        print("❌ 无效的分类")
        sys.exit(1)

    # 输入标签
    tags_input = input("\n🏷️  请输入标签（用逗号分隔，可选）：").strip()
    tags = [t.strip() for t in tags_input.split(",")] if tags_input else []

    # 选择优先级
    print("\n⭐ 请选择优先级：")
    print("  1. high（高）")
    print("  2. medium（中）")
    print("  3. low（低）")

    priority_input = input("请输入优先级编号（默认：medium）：").strip()
    if not priority_input or priority_input == "2":
        priority = "medium"
    elif priority_input == "1":
        priority = "high"
    elif priority_input == "3":
        priority = "low"
    else:
        print("❌ 无效的优先级")
        sys.exit(1)

    # 记录日志
    print()
    log_entry(content, category, tags, priority)


def main():
    """主函数"""
    if len(sys.argv) == 1:
        # 无参数，进入交互模式
        interactive_mode()
    else:
        # 命令行参数模式
        import argparse

        parser = argparse.ArgumentParser(description="生活秘书 - 记录生活日志")
        parser.add_argument("content", help="记录内容")
        parser.add_argument("-c", "--category", default="event",
                          choices=list(CATEGORIES.keys()), help="分类")
        parser.add_argument("-t", "--tags", nargs="+", help="标签列表")
        parser.add_argument("-p", "--priority", default="medium",
                          choices=PRIORITIES, help="优先级")

        args = parser.parse_args()
        log_entry(args.content, args.category, args.tags, args.priority)


if __name__ == "__main__":
    main()
