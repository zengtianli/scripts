#!/usr/bin/env python3
"""秘书系统 - 统一日志记录入口"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 日志文件路径
LOG_DIR = Path.home() / "Library" / "Logs" / "secretary"

# 日志类型配置
LOG_TYPES = {
    "1": {
        "name": "工作日志",
        "icon": "💼",
        "file": "work_log.jsonl",
        "secretary": "work",
        "categories": {
            "1": "project_progress",
            "2": "meeting",
            "3": "task",
            "4": "code_review",
            "5": "documentation",
            "6": "bug_fix",
            "7": "deployment",
            "8": "planning",
        },
        "extra_fields": ["project_id", "files"],
    },
    "2": {
        "name": "个人发展",
        "icon": "🌟",
        "file": "personal_log.jsonl",
        "secretary": "personal",
        "categories": {
            "1": "investment",
            "2": "learning",
            "3": "health",
            "4": "social",
            "5": "family",
            "6": "hobby",
            "7": "reading",
            "8": "other",
        },
        "extra_fields": [],
    },
    "3": {
        "name": "投资记录",
        "icon": "💰",
        "file": "investment_log.jsonl",
        "secretary": "investment",
        "categories": {"1": "watch", "2": "buy", "3": "sell", "4": "hold", "5": "analysis"},
        "extra_fields": ["ticker", "price", "quantity"],
    },
    "4": {
        "name": "学习记录",
        "icon": "📚",
        "file": "learning_log.jsonl",
        "secretary": "learning",
        "categories": {"1": "course", "2": "book", "3": "article", "4": "video", "5": "practice", "6": "project"},
        "extra_fields": ["topic", "progress", "source"],
    },
    "5": {
        "name": "生活记录",
        "icon": "🏡",
        "file": "life_log.jsonl",
        "secretary": "life",
        "categories": {
            "1": "health",
            "2": "exercise",
            "3": "diet",
            "4": "sleep",
            "5": "mood",
            "6": "event",
            "7": "shopping",
            "8": "other",
        },
        "extra_fields": ["location", "duration", "cost"],
    },
}

PRIORITIES = {"1": "high", "2": "medium", "3": "low"}


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]"
    value = input(f"{prompt}: ").strip()
    return value if value else default


def select_log_type():
    """选择日志类型"""
    print("📝 秘书系统 - 统一日志记录\n")
    print("请选择日志类型：")
    for key, config in LOG_TYPES.items():
        print(f"  {key}. {config['icon']} {config['name']}")

    type_key = get_input("\n选择类型", "1")
    return LOG_TYPES.get(type_key, LOG_TYPES["1"])


def record_log(log_config):
    """记录日志"""
    print(f"\n{log_config['icon']} {log_config['name']}\n")

    # 获取内容
    content = get_input("记录内容")
    if not content:
        print("❌ 内容不能为空")
        sys.exit(1)

    # 获取分类
    print("\n分类选择：")
    for key, value in log_config["categories"].items():
        print(f"  {key}. {value}")
    category_key = get_input("选择分类", "1")
    category = log_config["categories"].get(category_key, list(log_config["categories"].values())[0])

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

    # 根据日志类型获取特定字段
    if log_config["secretary"] == "work":
        project_id = get_input("项目 ID（可选）", "")
        if project_id:
            metadata["project_id"] = project_id
        files_input = get_input("相关文件路径（逗号分隔，可选）", "")
        if files_input:
            files = [f.strip() for f in files_input.split(",") if f.strip()]
            metadata["files"] = files

    elif log_config["secretary"] == "investment":
        ticker = get_input("股票代码/币种（可选）", "")
        if ticker:
            metadata["ticker"] = ticker
        price = get_input("价格（可选）", "")
        if price:
            metadata["price"] = price
        quantity = get_input("数量（可选）", "")
        if quantity:
            metadata["quantity"] = quantity

    elif log_config["secretary"] == "learning":
        topic = get_input("学习主题（可选）", "")
        if topic:
            metadata["topic"] = topic
        progress = get_input("进度（可选）", "")
        if progress:
            metadata["progress"] = progress
        source = get_input("来源（可选）", "")
        if source:
            metadata["source"] = source

    elif log_config["secretary"] == "life":
        location = get_input("地点（可选）", "")
        if location:
            metadata["location"] = location
        duration = get_input("时长（可选）", "")
        if duration:
            metadata["duration"] = duration
        cost = get_input("花费（可选）", "")
        if cost:
            metadata["cost"] = cost

    # 构建日志条目
    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "secretary": log_config["secretary"],
        "category": category,
        "content": content,
        "tags": tags,
        "priority": priority,
        "metadata": metadata,
    }

    # 确保日志目录存在
    log_file = LOG_DIR / log_config["file"]
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 追加到日志文件
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    print(f"\n✅ {log_config['name']}已保存")
    print(f"   分类: {category}")
    print(f"   优先级: {priority}")
    print(f"   标签: {', '.join(tags) if tags else '无'}")


def main():
    log_config = select_log_type()
    record_log(log_config)


if __name__ == "__main__":
    main()
