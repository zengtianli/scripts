#!/usr/bin/env python3
"""综合秘书 - 记录个人发展相关内容"""

import json
import sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "personal_log.jsonl"

CATEGORIES = {
    "1": "investment",
    "2": "learning",
    "3": "health",
    "4": "social",
    "5": "family",
    "6": "hobby",
    "7": "reading",
    "8": "other"
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
    print("🌟 综合秘书 - 记录个人发展\n")

    # 获取内容
    content = get_input("记录内容")
    if not content:
        print("❌ 内容不能为空")
        sys.exit(1)

    # 获取分类
    print("\n分类选择：")
    for key, value in CATEGORIES.items():
        print(f"  {key}. {value}")
    category_key = get_input("选择分类", "1")
    category = CATEGORIES.get(category_key, "other")

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

    # 根据分类获取特定字段
    if category == "investment":
        ticker = get_input("股票代码/币种（可选）", "")
        if ticker:
            metadata["ticker"] = ticker
        action = get_input("操作类型（watch/buy/sell/hold）", "watch")
        if action:
            metadata["action"] = action

    elif category == "learning":
        topic = get_input("学习主题（可选）", "")
        if topic:
            metadata["topic"] = topic
        progress = get_input("进度（可选，如：第3章）", "")
        if progress:
            metadata["progress"] = progress

    elif category == "health":
        activity_type = get_input("活动类型（可选，如：跑步/健身/睡眠）", "")
        if activity_type:
            metadata["activity_type"] = activity_type
        duration = get_input("时长/数据（可选，如：5km/8小时）", "")
        if duration:
            metadata["duration"] = duration

    elif category == "reading":
        book_title = get_input("书名（可选）", "")
        if book_title:
            metadata["book_title"] = book_title
        pages = get_input("页数/章节（可选）", "")
        if pages:
            metadata["pages"] = pages

    # 构建日志条目
    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "secretary": "personal",
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

    print(f"\n✅ 综合记录已保存")
    print(f"   分类: {category}")
    print(f"   优先级: {priority}")
    print(f"   标签: {', '.join(tags) if tags else '无'}")


if __name__ == "__main__":
    main()
