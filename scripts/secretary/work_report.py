#!/usr/bin/env python3
"""工作秘书 - 生成工作报告"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "work_log.jsonl"


def load_logs(days=7):
    """加载最近 N 天的日志"""
    if not LOG_FILE.exists():
        return []

    cutoff_date = datetime.now().astimezone() - timedelta(days=days)
    logs = []

    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                timestamp = datetime.fromisoformat(entry["timestamp"])
                if timestamp >= cutoff_date:
                    logs.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return logs


def format_entry(entry):
    """格式化单条记录"""
    timestamp = datetime.fromisoformat(entry["timestamp"])
    time_str = timestamp.strftime("%m-%d %H:%M")
    content = entry["content"]
    tags = " ".join([f"#{tag}" for tag in entry.get("tags", [])])
    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(entry.get("priority", "medium"), "🟡")

    # 添加项目信息
    project_info = ""
    if "metadata" in entry and "project_id" in entry["metadata"]:
        project_info = f" [项目: {entry['metadata']['project_id']}]"

    return f"- [{time_str}] {priority_icon} {content}{project_info} {tags}"


def generate_report(days=7):
    """生成工作报告"""
    logs = load_logs(days)

    if not logs:
        print(f"💼 最近 {days} 天没有工作记录")
        return

    # 按优先级分组
    by_priority = defaultdict(list)
    for entry in logs:
        priority = entry.get("priority", "medium")
        by_priority[priority].append(entry)

    # 按标签分组
    by_tag = defaultdict(list)
    for entry in logs:
        for tag in entry.get("tags", []):
            by_tag[tag].append(entry)

    # 按分类分组
    by_category = defaultdict(list)
    for entry in logs:
        category = entry.get("category", "unknown")
        by_category[category].append(entry)

    # 按项目分组
    by_project = defaultdict(list)
    for entry in logs:
        if "metadata" in entry and "project_id" in entry["metadata"]:
            project_id = entry["metadata"]["project_id"]
            by_project[project_id].append(entry)

    # 生成报告
    print(f"# 💼 工作报告（最近 {days} 天）\n")
    print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("## 📈 概览\n")
    print(f"- 总记录数：{len(logs)}")
    print(f"- 高优先级：{len(by_priority['high'])}")
    print(f"- 中优先级：{len(by_priority['medium'])}")
    print(f"- 低优先级：{len(by_priority['low'])}")
    print(f"- 涉及项目：{len(by_project)}")
    print(f"- 涉及标签：{len(by_tag)}\n")

    # 按项目展示
    if by_project:
        print("## 📁 按项目\n")
        for project_id, entries in sorted(by_project.items()):
            print(f"### {project_id} ({len(entries)})\n")
            for entry in sorted(entries, key=lambda x: x["timestamp"], reverse=True):
                print(format_entry(entry))
            print()

    # 按优先级展示
    print("## 🎯 按优先级\n")
    for priority in ["high", "medium", "low"]:
        if by_priority[priority]:
            priority_name = {"high": "高优先级", "medium": "中优先级", "low": "低优先级"}[priority]
            print(f"### {priority_name}\n")
            for entry in sorted(by_priority[priority], key=lambda x: x["timestamp"], reverse=True):
                print(format_entry(entry))
            print()

    # 按分类展示
    print("## 📂 按分类\n")
    category_names = {
        "project_progress": "项目进展",
        "meeting": "会议",
        "task": "任务",
        "code_review": "代码审查",
        "documentation": "文档",
        "bug_fix": "Bug 修复",
        "deployment": "部署",
        "planning": "规划",
    }
    for category, entries in sorted(by_category.items()):
        category_name = category_names.get(category, category)
        print(f"### {category_name} ({len(entries)})\n")
        for entry in sorted(entries, key=lambda x: x["timestamp"], reverse=True):
            print(format_entry(entry))
        print()

    # 按标签展示（只显示出现次数 >= 2 的标签）
    popular_tags = {tag: entries for tag, entries in by_tag.items() if len(entries) >= 2}
    if popular_tags:
        print("## 🏷️ 热门标签\n")
        for tag, entries in sorted(popular_tags.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"### #{tag} ({len(entries)})\n")
            for entry in sorted(entries, key=lambda x: x["timestamp"], reverse=True):
                print(format_entry(entry))
            print()


def main():
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            print("❌ 参数必须是数字")
            sys.exit(1)
    else:
        days = 7

    generate_report(days)


if __name__ == "__main__":
    main()
