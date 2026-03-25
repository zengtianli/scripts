#!/usr/bin/env python3
"""秘书系统 - 统一报告入口"""

import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
sys.path.insert(0, str(Path(__file__).parent))

# 日志文件路径
LOG_DIR = Path.home() / "Library" / "Logs" / "secretary"

# 报告类型配置
REPORT_TYPES = {
    "1": {
        "name": "工作报告",
        "icon": "💼",
        "file": "work_log.jsonl",
        "secretary": "work",
        "category_names": {
            "project_progress": "项目进展",
            "meeting": "会议",
            "task": "任务",
            "code_review": "代码审查",
            "documentation": "文档",
            "bug_fix": "Bug 修复",
            "deployment": "部署",
            "planning": "规划",
        },
    },
    "2": {
        "name": "个人报告",
        "icon": "🌟",
        "file": "personal_log.jsonl",
        "secretary": "personal",
        "category_names": {
            "investment": "投资",
            "learning": "学习",
            "health": "健康",
            "social": "社交",
            "family": "家庭",
            "hobby": "爱好",
            "reading": "阅读",
            "other": "其他",
        },
    },
    "3": {
        "name": "投资报告",
        "icon": "💰",
        "file": "investment_log.jsonl",
        "secretary": "investment",
        "category_names": {"watch": "观察", "buy": "买入", "sell": "卖出", "hold": "持有", "analysis": "分析"},
    },
    "4": {
        "name": "学习报告",
        "icon": "📚",
        "file": "learning_log.jsonl",
        "secretary": "learning",
        "category_names": {
            "course": "课程",
            "book": "书籍",
            "article": "文章",
            "video": "视频",
            "practice": "实践",
            "project": "项目",
        },
    },
    "5": {
        "name": "生活报告",
        "icon": "🏡",
        "file": "life_log.jsonl",
        "secretary": "life",
        "category_names": {
            "health": "健康",
            "exercise": "运动",
            "diet": "饮食",
            "sleep": "睡眠",
            "mood": "心情",
            "event": "事件",
            "shopping": "购物",
            "other": "其他",
        },
    },
    "6": {"name": "每日报告", "icon": "📊", "file": "all", "secretary": "daily", "category_names": {}},
}

# 时间范围配置
TIME_RANGES = {
    "1": {"name": "今天", "days": 0},
    "2": {"name": "昨天", "days": 1},
    "3": {"name": "最近 3 天", "days": 3},
    "4": {"name": "本周", "days": 7},
    "5": {"name": "本月", "days": 30},
}


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]"
    value = input(f"{prompt}: ").strip()
    return value if value else default


def select_report_type():
    """选择报告类型"""
    print("📊 秘书系统 - 统一报告\n")
    print("请选择报告类型：")
    for key, config in REPORT_TYPES.items():
        print(f"  {key}. {config['icon']} {config['name']}")

    type_key = get_input("\n选择类型", "1")
    return REPORT_TYPES.get(type_key, REPORT_TYPES["1"])


def select_time_range():
    """选择时间范围"""
    print("\n请选择时间范围：")
    for key, config in TIME_RANGES.items():
        print(f"  {key}. {config['name']}")

    range_key = get_input("\n选择范围", "3")
    return TIME_RANGES.get(range_key, TIME_RANGES["3"])


def load_logs(log_file, days):
    """加载日志"""
    if not log_file.exists():
        return []

    if days == 0:
        # 今天
        cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif days == 1:
        # 昨天
        yesterday = datetime.now() - timedelta(days=1)
        cutoff_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        # 最近 N 天
        cutoff_date = datetime.now() - timedelta(days=days)
        end_date = None

    logs = []
    with open(log_file, encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                timestamp_str = entry["timestamp"]

                # 处理 ISO 8601 格式的时间戳
                if isinstance(timestamp_str, str):
                    # 移除时区信息以进行比较
                    if "+" in timestamp_str:
                        timestamp_str = timestamp_str.split("+")[0]
                    elif timestamp_str.endswith("Z"):
                        timestamp_str = timestamp_str[:-1]
                    timestamp = datetime.fromisoformat(timestamp_str)
                else:
                    timestamp = datetime.fromisoformat(str(timestamp_str))

                if days == 1:
                    # 昨天：需要在范围内
                    if cutoff_date <= timestamp <= end_date:
                        logs.append(entry)
                else:
                    # 今天或最近 N 天
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

    # 添加元数据信息
    metadata_info = ""
    if "metadata" in entry:
        meta = entry["metadata"]
        if "project_id" in meta:
            metadata_info += f" [项目: {meta['project_id']}]"
        if "ticker" in meta:
            metadata_info += f" [代码: {meta['ticker']}]"
        if "topic" in meta:
            metadata_info += f" [主题: {meta['topic']}]"

    return f"- [{time_str}] {priority_icon} {content}{metadata_info} {tags}"


def generate_report(report_config, time_range):
    """生成报告"""
    print(f"\n{report_config['icon']} {report_config['name']} - {time_range['name']}\n")

    # 加载日志
    log_file = LOG_DIR / report_config["file"]
    logs = load_logs(log_file, time_range["days"])

    if not logs:
        print(f"📭 {time_range['name']}没有记录")
        return

    # 按优先级分组
    by_priority = defaultdict(list)
    for entry in logs:
        priority = entry.get("priority", "medium")
        by_priority[priority].append(entry)

    # 按分类分组
    by_category = defaultdict(list)
    for entry in logs:
        category = entry.get("category", "unknown")
        by_category[category].append(entry)

    # 按标签分组
    by_tag = defaultdict(list)
    for entry in logs:
        for tag in entry.get("tags", []):
            by_tag[tag].append(entry)

    # 生成报告
    print(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    print("## 📈 概览\n")
    print(f"- 总记录数：{len(logs)}")
    print(f"- 高优先级：{len(by_priority['high'])}")
    print(f"- 中优先级：{len(by_priority['medium'])}")
    print(f"- 低优先级：{len(by_priority['low'])}")
    print(f"- 涉及分类：{len(by_category)}")
    print(f"- 涉及标签：{len(by_tag)}\n")

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
    for category, entries in sorted(by_category.items()):
        category_name = report_config["category_names"].get(category, category)
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


def generate_daily_report(time_range):
    """生成每日综合报告"""
    print(f"\n📊 每日综合报告 - {time_range['name']}\n")

    # 导入每日报告模块
    try:
        from daily_report import generate_report as gen_daily

        # 调用原有的每日报告功能
        gen_daily()
    except ImportError:
        print("❌ 每日报告模块未找到")


def main():
    # 支持命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="秘书系统 - 统一报告")
    parser.add_argument("--type", help="报告类型 (1-6)", default=None)
    parser.add_argument("--range", help="时间范围 (1-5)", default=None)
    args = parser.parse_args()

    # 选择报告类型
    if args.type and args.type in REPORT_TYPES:
        report_config = REPORT_TYPES[args.type]
    else:
        report_config = select_report_type()

    # 选择时间范围
    if args.range and args.range in TIME_RANGES:
        time_range = TIME_RANGES[args.range]
    else:
        time_range = select_time_range()

    # 每日报告使用特殊逻辑
    if report_config["secretary"] == "daily":
        generate_daily_report(time_range)
    else:
        generate_report(report_config, time_range)


if __name__ == "__main__":
    main()
