#!/usr/bin/env python3
"""
应用使用报告生成器
分析 work_tracker.jsonl 数据，生成使用统计报告
"""

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path


def load_data(log_file, start_time, end_time):
    """加载指定时间范围的数据"""
    records = []

    if not log_file.exists():
        return records

    with open(log_file) as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                timestamp = record.get("timestamp")
                if start_time <= timestamp < end_time:
                    records.append(record)
            except json.JSONDecodeError:
                continue

    return records


def calculate_usage(records):
    """计算应用使用时长（分钟）"""
    app_minutes = defaultdict(int)

    for record in records:
        app = record.get("app", "Unknown")
        app_minutes[app] += 1  # 每条记录代表 1 分钟

    return dict(app_minutes)


def calculate_hourly_distribution(records):
    """计算时间分布（按小时）"""
    hourly_count = defaultdict(int)

    for record in records:
        timestamp = record.get("timestamp")
        hour = datetime.fromtimestamp(timestamp).hour
        hourly_count[hour] += 1

    return dict(hourly_count)


def calculate_focus_score(records):
    """计算专注度评分（0-100）
    基于：单应用连续使用时长占比
    """
    if not records:
        return 0

    # 按时间排序
    sorted_records = sorted(records, key=lambda x: x["timestamp"])

    # 计算连续使用时长
    continuous_blocks = []
    current_app = None
    current_duration = 0

    for record in sorted_records:
        app = record.get("app")
        if app == current_app:
            current_duration += 1
        else:
            if current_duration > 0:
                continuous_blocks.append(current_duration)
            current_app = app
            current_duration = 1

    if current_duration > 0:
        continuous_blocks.append(current_duration)

    # 专注度 = 平均连续时长 / 总时长 * 100
    if continuous_blocks:
        avg_continuous = sum(continuous_blocks) / len(continuous_blocks)
        total_minutes = len(records)
        focus_score = min(100, (avg_continuous / total_minutes) * 100 * 10)
        return round(focus_score, 1)

    return 0


def generate_report(records, period_name):
    """生成 Markdown 报告"""
    if not records:
        print(f"# {period_name} 应用使用报告\n")
        print("暂无数据")
        return

    # 计算指标
    app_usage = calculate_usage(records)
    hourly_dist = calculate_hourly_distribution(records)
    focus_score = calculate_focus_score(records)

    # 排序
    top_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:10]

    # 输出报告
    print(f"# {period_name} 应用使用报告\n")

    # 总览
    total_minutes = len(records)
    total_hours = total_minutes / 60
    print(f"**总使用时长**: {total_hours:.1f} 小时 ({total_minutes} 分钟)")
    print(f"**专注度评分**: {focus_score}/100\n")

    # Top 应用
    print("## Top 10 应用\n")
    print("| 排名 | 应用 | 时长（分钟） | 时长（小时） | 占比 |")
    print("|------|------|--------------|--------------|------|")

    for idx, (app, minutes) in enumerate(top_apps, 1):
        hours = minutes / 60
        percentage = (minutes / total_minutes) * 100
        print(f"| {idx} | {app} | {minutes} | {hours:.1f} | {percentage:.1f}% |")

    # 时间分布
    print("\n## 时间分布\n")
    print("| 时段 | 使用次数 |")
    print("|------|----------|")

    for hour in range(24):
        count = hourly_dist.get(hour, 0)
        if count > 0:
            bar = "█" * (count // 10 + 1)
            print(f"| {hour:02d}:00 | {bar} ({count}) |")


def main():
    parser = argparse.ArgumentParser(description="生成应用使用报告")
    parser.add_argument("--today", action="store_true", help="今日报告")
    parser.add_argument("--week", action="store_true", help="本周报告")

    args = parser.parse_args()

    # 确定时间范围
    now = datetime.now()
    if args.today:
        start = datetime(now.year, now.month, now.day, 0, 0, 0)
        end = now
        period_name = "今日"
    elif args.week:
        # 本周一到现在
        days_since_monday = now.weekday()
        start = datetime(now.year, now.month, now.day, 0, 0, 0) - timedelta(days=days_since_monday)
        end = now
        period_name = "本周"
    else:
        print("请指定 --today 或 --week")
        return

    # 加载数据
    log_file = Path.home() / "Library" / "Logs" / "work_tracker.jsonl"
    records = load_data(log_file, int(start.timestamp()), int(end.timestamp()))

    # 生成报告
    generate_report(records, period_name)


if __name__ == "__main__":
    main()
