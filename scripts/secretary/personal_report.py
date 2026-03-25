#!/usr/bin/env python3
"""综合秘书报告 - 查看个人发展记录"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "personal_log.jsonl"


def load_logs():
    """加载日志文件"""
    if not LOG_FILE.exists():
        return []

    logs = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return logs


def filter_by_date(logs, days=None):
    """按日期筛选"""
    if days is None:
        return logs

    cutoff = datetime.now().astimezone() - timedelta(days=days)
    filtered = []
    for log in logs:
        try:
            log_time = datetime.fromisoformat(log["timestamp"])
            if log_time >= cutoff:
                filtered.append(log)
        except (ValueError, KeyError):
            continue
    return filtered


def filter_by_category(logs, category=None):
    """按分类筛选"""
    if category is None:
        return logs
    return [log for log in logs if log.get("category") == category]


def filter_by_priority(logs, priority=None):
    """按优先级筛选"""
    if priority is None:
        return logs
    return [log for log in logs if log.get("priority") == priority]


def print_summary(logs):
    """打印统计摘要"""
    if not logs:
        print("📊 暂无记录\n")
        return

    # 按分类统计
    by_category = defaultdict(int)
    by_priority = defaultdict(int)

    for log in logs:
        by_category[log.get("category", "unknown")] += 1
        by_priority[log.get("priority", "unknown")] += 1

    print(f"📊 统计摘要（共 {len(logs)} 条记录）\n")

    print("按分类：")
    for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")

    print("\n按优先级：")
    for priority, count in sorted(by_priority.items(), key=lambda x: x[1], reverse=True):
        print(f"  {priority}: {count}")
    print()


def print_logs(logs, limit=None):
    """打印日志列表"""
    if not logs:
        print("📝 暂无记录\n")
        return

    # 按时间倒序排列
    logs_sorted = sorted(logs, key=lambda x: x.get("timestamp", ""), reverse=True)

    if limit:
        logs_sorted = logs_sorted[:limit]

    print(f"📝 记录列表（最近 {len(logs_sorted)} 条）\n")

    for log in logs_sorted:
        timestamp = log.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(timestamp)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            time_str = timestamp

        category = log.get("category", "unknown")
        priority = log.get("priority", "medium")
        content = log.get("content", "")
        tags = log.get("tags", [])
        metadata = log.get("metadata", {})

        # 优先级图标
        priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")

        print(f"{priority_icon} [{time_str}] {category}")
        print(f"   {content}")

        if tags:
            print(f"   标签: {', '.join(tags)}")

        if metadata:
            meta_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
            print(f"   详情: {meta_str}")

        print()


def main():
    print("🌟 综合秘书报告\n")

    # 加载日志
    logs = load_logs()

    if not logs:
        print("❌ 暂无记录")
        sys.exit(0)

    # 选择查看方式
    print("查看方式：")
    print("  1. 今天")
    print("  2. 最近 7 天")
    print("  3. 最近 30 天")
    print("  4. 全部")
    print("  5. 按分类筛选")
    print("  6. 按优先级筛选")

    choice = input("\n选择 [1]: ").strip() or "1"

    if choice == "1":
        logs = filter_by_date(logs, days=1)
        print("\n=== 今天的记录 ===\n")
    elif choice == "2":
        logs = filter_by_date(logs, days=7)
        print("\n=== 最近 7 天的记录 ===\n")
    elif choice == "3":
        logs = filter_by_date(logs, days=30)
        print("\n=== 最近 30 天的记录 ===\n")
    elif choice == "4":
        print("\n=== 全部记录 ===\n")
    elif choice == "5":
        print("\n分类选择：")
        categories = set(log.get("category") for log in logs if log.get("category"))
        for i, cat in enumerate(sorted(categories), 1):
            print(f"  {i}. {cat}")
        cat_choice = input("\n选择分类: ").strip()
        if cat_choice.isdigit():
            cat_list = sorted(categories)
            idx = int(cat_choice) - 1
            if 0 <= idx < len(cat_list):
                category = cat_list[idx]
                logs = filter_by_category(logs, category)
                print(f"\n=== {category} 记录 ===\n")
    elif choice == "6":
        print("\n优先级选择：")
        print("  1. high")
        print("  2. medium")
        print("  3. low")
        pri_choice = input("\n选择优先级 [2]: ").strip() or "2"
        priority_map = {"1": "high", "2": "medium", "3": "low"}
        priority = priority_map.get(pri_choice, "medium")
        logs = filter_by_priority(logs, priority)
        print(f"\n=== {priority} 优先级记录 ===\n")

    # 显示统计
    print_summary(logs)

    # 显示记录列表
    limit_input = input("显示最近多少条？[20]: ").strip()
    limit = int(limit_input) if limit_input.isdigit() else 20
    print_logs(logs, limit=limit)


if __name__ == "__main__":
    main()
