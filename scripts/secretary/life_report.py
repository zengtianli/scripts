#!/usr/bin/env python3
"""
生活秘书 - 生成生活报告
按时间、按类别分类展示生活日志
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "life_log.jsonl"

CATEGORIES = {
    "health": "🏃 健康",
    "social": "👥 社交",
    "family": "👨‍👩‍👧‍👦 家庭",
    "hobby": "🎨 爱好",
    "todo": "✅ 待办",
    "event": "📅 事件",
}


def load_logs(days: int = 7) -> list[dict]:
    """加载指定天数内的日志"""
    if not LOG_FILE.exists():
        return []

    cutoff_date = datetime.now().astimezone() - timedelta(days=days)
    logs = []

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry["timestamp"])
                if entry_time >= cutoff_date:
                    logs.append(entry)

    return logs


def format_timestamp(iso_timestamp: str) -> str:
    """格式化时间戳"""
    dt = datetime.fromisoformat(iso_timestamp)
    return dt.strftime("%m-%d %H:%M")


def generate_report_by_time(logs: list[dict]) -> str:
    """按时间顺序生成报告"""
    if not logs:
        return "📭 暂无生活记录\n"

    # 按日期分组
    logs_by_date = defaultdict(list)
    for log in logs:
        dt = datetime.fromisoformat(log["timestamp"])
        date_key = dt.strftime("%Y-%m-%d")
        logs_by_date[date_key].append(log)

    # 生成报告
    report = []
    report.append("# 生活日志 - 按时间排序\n")

    for date in sorted(logs_by_date.keys(), reverse=True):
        report.append(f"## {date}\n")
        day_logs = sorted(logs_by_date[date], key=lambda x: x["timestamp"], reverse=True)

        for log in day_logs:
            time_str = format_timestamp(log["timestamp"])
            category_icon = CATEGORIES.get(log["category"], "📝")
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(log["priority"], "⚪")

            report.append(f"### [{time_str}] {category_icon} {log['content']}")

            if log.get("tags"):
                tags_str = " ".join([f"#{tag}" for tag in log["tags"]])
                report.append(f"**标签**: {tags_str}")

            report.append(f"**优先级**: {priority_icon} {log['priority']}\n")

    return "\n".join(report)


def generate_report_by_category(logs: list[dict]) -> str:
    """按类别生成报告"""
    if not logs:
        return "📭 暂无生活记录\n"

    # 按类别分组
    logs_by_category = defaultdict(list)
    for log in logs:
        logs_by_category[log["category"]].append(log)

    # 生成报告
    report = []
    report.append("# 生活日志 - 按类别分类\n")

    # 统计信息
    report.append("## 📊 统计概览\n")
    for category in sorted(logs_by_category.keys()):
        count = len(logs_by_category[category])
        category_name = CATEGORIES.get(category, category)
        report.append(f"- {category_name}: {count} 条")
    report.append(f"- **总计**: {len(logs)} 条\n")

    # 按类别展示
    for category in sorted(logs_by_category.keys()):
        category_name = CATEGORIES.get(category, category)
        report.append(f"## {category_name}\n")

        category_logs = sorted(logs_by_category[category], key=lambda x: x["timestamp"], reverse=True)

        for log in category_logs:
            time_str = format_timestamp(log["timestamp"])
            priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(log["priority"], "⚪")

            report.append(f"### [{time_str}] {log['content']}")

            if log.get("tags"):
                tags_str = " ".join([f"#{tag}" for tag in log["tags"]])
                report.append(f"**标签**: {tags_str}")

            report.append(f"**优先级**: {priority_icon} {log['priority']}\n")

    return "\n".join(report)


def generate_summary(logs: list[dict]) -> str:
    """生成简要统计"""
    if not logs:
        return "📭 暂无生活记录"

    # 统计信息
    total = len(logs)
    by_category = defaultdict(int)
    by_priority = defaultdict(int)

    for log in logs:
        by_category[log["category"]] += 1
        by_priority[log["priority"]] += 1

    # 生成报告
    lines = []
    lines.append(f"📊 生活日志统计（最近 {total} 条）\n")

    lines.append("按类别：")
    for category, count in sorted(by_category.items(), key=lambda x: -x[1]):
        category_name = CATEGORIES.get(category, category)
        lines.append(f"  {category_name}: {count} 条")

    lines.append("\n按优先级：")
    for priority in ["high", "medium", "low"]:
        if priority in by_priority:
            icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}[priority]
            lines.append(f"  {icon} {priority}: {by_priority[priority]} 条")

    return "\n".join(lines)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="生活秘书 - 生成生活报告")
    parser.add_argument("-d", "--days", type=int, default=7, help="查看最近几天的记录（默认：7）")
    parser.add_argument(
        "-m", "--mode", choices=["time", "category", "summary"], default="time", help="报告模式（默认：time）"
    )

    args = parser.parse_args()

    # 加载日志
    logs = load_logs(args.days)

    # 生成报告
    if args.mode == "time":
        report = generate_report_by_time(logs)
    elif args.mode == "category":
        report = generate_report_by_category(logs)
    else:  # summary
        report = generate_summary(logs)

    print(report)


if __name__ == "__main__":
    main()
