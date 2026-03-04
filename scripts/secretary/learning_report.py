#!/usr/bin/env python3
"""
学习秘书 - 生成学习报告
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# 日志文件路径
LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "learning_log.jsonl"

# 分类中文名称
CATEGORY_NAMES = {
    "reading": "📚 阅读",
    "course": "🎓 课程",
    "practice": "💻 实践",
    "insight": "💡 灵感",
    "paper": "📄 论文"
}

# 优先级中文名称
PRIORITY_NAMES = {
    "high": "🔴 高",
    "medium": "🟡 中",
    "low": "🟢 低"
}


def load_logs(days=7):
    """加载最近 N 天的日志"""
    if not LOG_FILE.exists():
        return []

    cutoff_date = datetime.now().astimezone() - timedelta(days=days)
    logs = []

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= cutoff_date:
                    entry["datetime"] = timestamp
                    logs.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return sorted(logs, key=lambda x: x["datetime"], reverse=True)


def generate_report_by_time(logs):
    """按时间生成报告"""
    print("\n" + "=" * 60)
    print("📅 按时间排序")
    print("=" * 60 + "\n")

    for entry in logs:
        dt = entry["datetime"]
        date_str = dt.strftime("%Y-%m-%d %H:%M")
        category = CATEGORY_NAMES.get(entry["category"], entry["category"])
        priority = PRIORITY_NAMES.get(entry["priority"], entry["priority"])

        print(f"[{date_str}] {category} {priority}")
        print(f"  {entry['content']}")

        if entry.get("tags"):
            print(f"  标签: {', '.join(entry['tags'])}")

        if entry.get("metadata"):
            metadata = entry["metadata"]
            if "book" in metadata:
                print(f"  书名: {metadata['book']}")
            if "course" in metadata:
                print(f"  课程: {metadata['course']}")
            if "project" in metadata:
                print(f"  项目: {metadata['project']}")
            if "progress" in metadata:
                print(f"  进度: {metadata['progress']}")

        print()


def generate_report_by_category(logs):
    """按分类生成报告"""
    print("\n" + "=" * 60)
    print("📊 按分类统计")
    print("=" * 60 + "\n")

    by_category = defaultdict(list)
    for entry in logs:
        by_category[entry["category"]].append(entry)

    for category, entries in sorted(by_category.items()):
        category_name = CATEGORY_NAMES.get(category, category)
        print(f"{category_name} ({len(entries)} 条)")
        print("-" * 60)

        for entry in entries:
            dt = entry["datetime"]
            date_str = dt.strftime("%m-%d %H:%M")
            priority = PRIORITY_NAMES.get(entry["priority"], entry["priority"])
            print(f"  [{date_str}] {priority} {entry['content'][:50]}...")

        print()


def generate_report_by_tags(logs):
    """按标签生成报告"""
    print("\n" + "=" * 60)
    print("🏷️  按标签统计")
    print("=" * 60 + "\n")

    by_tags = defaultdict(int)
    for entry in logs:
        for tag in entry.get("tags", []):
            by_tags[tag] += 1

    if not by_tags:
        print("暂无标签数据\n")
        return

    sorted_tags = sorted(by_tags.items(), key=lambda x: x[1], reverse=True)
    for tag, count in sorted_tags[:20]:  # 显示前 20 个标签
        print(f"  {tag}: {count} 次")

    print()


def generate_statistics(logs):
    """生成统计信息"""
    print("\n" + "=" * 60)
    print("📈 统计概览")
    print("=" * 60 + "\n")

    total = len(logs)
    print(f"总记录数: {total}")

    # 按分类统计
    by_category = defaultdict(int)
    for entry in logs:
        by_category[entry["category"]] += 1

    print("\n分类分布:")
    for category, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
        category_name = CATEGORY_NAMES.get(category, category)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {category_name}: {count} 条 ({percentage:.1f}%)")

    # 按优先级统计
    by_priority = defaultdict(int)
    for entry in logs:
        by_priority[entry["priority"]] += 1

    print("\n优先级分布:")
    for priority in ["high", "medium", "low"]:
        count = by_priority[priority]
        priority_name = PRIORITY_NAMES.get(priority, priority)
        percentage = (count / total * 100) if total > 0 else 0
        print(f"  {priority_name}: {count} 条 ({percentage:.1f}%)")

    print()


def main():
    # 获取天数参数
    days = 7
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print(f"错误：无效的天数参数 '{sys.argv[1]}'")
            sys.exit(1)

    print(f"=== 学习秘书 - 最近 {days} 天学习报告 ===")

    # 加载日志
    logs = load_logs(days)

    if not logs:
        print(f"\n暂无最近 {days} 天的学习记录")
        return

    # 生成各类报告
    generate_statistics(logs)
    generate_report_by_category(logs)
    generate_report_by_tags(logs)
    generate_report_by_time(logs)


if __name__ == "__main__":
    main()
