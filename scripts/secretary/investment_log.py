#!/usr/bin/env python3
"""投资秘书 - 记录投资想法和决策"""

import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "investment_log.jsonl"

CATEGORIES = {
    "1": "stock_idea",
    "2": "crypto",
    "3": "macro",
    "4": "portfolio",
    "5": "research"
}

PRIORITIES = {
    "1": "high",
    "2": "medium",
    "3": "low"
}


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]"
    value = input(f"{prompt}: ").strip()
    return value if value else default


def main():
    print("📊 投资秘书 - 记录投资想法\n")

    # 获取内容
    content = get_input("投资内容")
    if not content:
        print("❌ 内容不能为空")
        sys.exit(1)

    # 获取分类
    print("\n分类选择：")
    for key, value in CATEGORIES.items():
        print(f"  {key}. {value}")
    category_key = get_input("选择分类", "1")
    category = CATEGORIES.get(category_key, "stock_idea")

    # 获取标签
    tags_input = get_input("标签（逗号分隔）", "")
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

    # 获取优先级
    print("\n优先级：")
    for key, value in PRIORITIES.items():
        print(f"  {key}. {value}")
    priority_key = get_input("选择优先级", "2")
    priority = PRIORITIES.get(priority_key, "medium")

    # 获取扩展信息
    metadata = {}
    if category in ["stock_idea", "crypto"]:
        ticker = get_input("股票代码/币种（可选）", "")
        if ticker:
            metadata["ticker"] = ticker
        action = get_input("操作类型（watch/buy/sell/hold）", "watch")
        if action:
            metadata["action"] = action

    # 构建日志条目
    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "category": category,
        "content": content,
        "tags": tags,
        "priority": priority,
        "metadata": metadata
    }

    # 确保日志目录存在
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 追加到日志文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"\n✅ 投资记录已保存")
    print(f"   分类: {category}")
    print(f"   优先级: {priority}")
    print(f"   标签: {', '.join(tags) if tags else '无'}")


if __name__ == "__main__":
    main()
