#!/usr/bin/env python3
"""
总秘书每日汇总脚本
整合应用追踪数据和三个秘书的日志，生成每日总结
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import argparse

# 数据路径
WORK_TRACKER_LOG = Path.home() / "Library/Logs/work_tracker.jsonl"
SECRETARY_DIR = Path.home() / "Library/Logs/secretary"
INVESTMENT_LOG = SECRETARY_DIR / "investment_log.jsonl"
LEARNING_LOG = SECRETARY_DIR / "learning_log.jsonl"
LIFE_LOG = SECRETARY_DIR / "life_log.jsonl"
SUMMARY_DIR = SECRETARY_DIR / "daily_summary"


def read_jsonl(file_path, date_str=None):
    """读取 JSONL 文件，可选按日期过滤"""
    if not file_path.exists():
        return []

    records = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if date_str:
                    # 过滤指定日期的记录
                    if 'timestamp' in record:
                        ts = record['timestamp']
                        if isinstance(ts, int):
                            # Unix timestamp
                            record_date = datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                        else:
                            # ISO 8601 format
                            record_date = ts.split('T')[0]
                        if record_date == date_str:
                            records.append(record)
                else:
                    records.append(record)
            except json.JSONDecodeError:
                continue
    return records


def analyze_app_usage(date_str):
    """分析应用使用情况"""
    records = read_jsonl(WORK_TRACKER_LOG, date_str)
    if not records:
        return {}

    # 统计每个应用的使用次数（每条记录代表 1 分钟）
    app_counts = defaultdict(int)
    for record in records:
        app = record.get('app', 'Unknown')
        app_counts[app] += 1

    # 转换为分钟数并排序
    app_usage = {app: count for app, count in app_counts.items()}
    sorted_usage = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)

    return dict(sorted_usage)


def format_time(minutes):
    """格式化时间显示"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def load_secretary_logs(date_str):
    """加载三个秘书的日志"""
    investment = read_jsonl(INVESTMENT_LOG, date_str)
    learning = read_jsonl(LEARNING_LOG, date_str)
    life = read_jsonl(LIFE_LOG, date_str)

    return {
        'investment': investment,
        'learning': learning,
        'life': life
    }


def generate_summary(date_str):
    """生成每日总结"""
    # 分析应用使用
    app_usage = analyze_app_usage(date_str)

    # 加载秘书日志
    logs = load_secretary_logs(date_str)

    # 生成 Markdown
    lines = []
    lines.append(f"# {date_str} 每日总结\n")

    # 今日概览
    lines.append("## 📊 今日概览\n")
    total_records = sum(len(logs[k]) for k in logs)
    lines.append(f"- 投资记录：{len(logs['investment'])} 条")
    lines.append(f"- 学习记录：{len(logs['learning'])} 条")
    lines.append(f"- 生活记录：{len(logs['life'])} 条")
    lines.append(f"- 总计：{total_records} 条\n")

    # 应用使用统计
    if app_usage:
        lines.append("## 💻 应用使用统计\n")
        total_minutes = sum(app_usage.values())
        lines.append(f"**总计工作时长**：{format_time(total_minutes)}\n")
        lines.append("**应用使用排行**：")
        for app, minutes in list(app_usage.items())[:10]:  # 只显示前 10
            percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
            lines.append(f"- {app}: {format_time(minutes)} ({percentage:.1f}%)")
        lines.append("")

    # 投资秘书
    if logs['investment']:
        lines.append("## 💰 投资秘书\n")
        # 按优先级分组
        by_priority = defaultdict(list)
        for record in logs['investment']:
            priority = record.get('priority', 'medium')
            by_priority[priority].append(record)

        for priority in ['high', 'medium', 'low']:
            if priority in by_priority:
                priority_name = {'high': '高优先级', 'medium': '中优先级', 'low': '低优先级'}[priority]
                lines.append(f"### {priority_name}")
                for record in by_priority[priority]:
                    ts = record.get('timestamp', '')
                    time_str = ts.split('T')[1][:5] if 'T' in ts else ''
                    content = record.get('content', '')
                    tags = ' '.join(f"#{tag}" for tag in record.get('tags', []))
                    lines.append(f"- [{time_str}] {content} {tags}")
                lines.append("")

    # 学习秘书
    if logs['learning']:
        lines.append("## 📚 学习秘书\n")
        lines.append("### 今日学习")
        for record in logs['learning']:
            ts = record.get('timestamp', '')
            time_str = ts.split('T')[1][:5] if 'T' in ts else ''
            content = record.get('content', '')
            tags = ' '.join(f"#{tag}" for tag in record.get('tags', []))
            lines.append(f"- [{time_str}] {content} {tags}")
        lines.append("")

    # 生活秘书
    if logs['life']:
        lines.append("## 🏃 生活秘书\n")
        # 按分类分组
        by_category = defaultdict(list)
        for record in logs['life']:
            category = record.get('category', 'other')
            by_category[category].append(record)

        category_names = {
            'health': '健康',
            'social': '社交',
            'family': '家庭',
            'hobby': '爱好',
            'todo': '待办事项',
            'event': '事件'
        }

        for category, name in category_names.items():
            if category in by_category:
                lines.append(f"### {name}")
                for record in by_category[category]:
                    ts = record.get('timestamp', '')
                    time_str = ts.split('T')[1][:5] if 'T' in ts else ''
                    content = record.get('content', '')
                    tags = ' '.join(f"#{tag}" for tag in record.get('tags', []))
                    lines.append(f"- [{time_str}] {content} {tags}")
                lines.append("")

    # 占位符：今日评估和明日计划
    lines.append("## 🎯 今日评估\n")
    lines.append("_使用 `hy_daily_review` 命令添加评估内容_\n")

    lines.append("## 📅 明日计划\n")
    lines.append("_使用 `hy_plan_tomorrow` 命令添加计划内容_\n")

    lines.append("---\n")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return '\n'.join(lines)


def save_summary(date_str, content):
    """保存总结到文件"""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SUMMARY_DIR / f"{date_str}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def show_summary(date_str):
    """显示总结"""
    summary = generate_summary(date_str)
    print(summary)

    # 保存到文件
    file_path = save_summary(date_str, summary)
    print(f"\n总结已保存到：{file_path}")


def add_plan(date_str):
    """添加明日计划"""
    print("请输入明日计划（每行一项，输入空行结束）：")
    plans = []
    while True:
        line = input()
        if not line:
            break
        plans.append(line)

    if not plans:
        print("未输入任何计划")
        return

    # 读取现有总结
    file_path = SUMMARY_DIR / f"{date_str}.md"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = generate_summary(date_str)

    # 替换明日计划部分
    plan_section = "## 📅 明日计划\n\n"
    for plan in plans:
        plan_section += f"- [ ] {plan}\n"
    plan_section += "\n"

    # 查找并替换
    if "## 📅 明日计划" in content:
        start = content.find("## 📅 明日计划")
        end = content.find("---", start)
        if end > start:
            content = content[:start] + plan_section + content[end:]

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n明日计划已添加到：{file_path}")


def add_review(date_str):
    """添加今日评估"""
    print("请输入今日评估：")
    print("1. 完成情况（如：计划完成度 80%）：")
    completion = input()
    print("2. 收获与反思：")
    reflection = input()
    print("3. 改进建议：")
    improvement = input()

    # 读取现有总结
    file_path = SUMMARY_DIR / f"{date_str}.md"
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = generate_summary(date_str)

    # 替换评估部分
    review_section = "## 🎯 今日评估\n\n"
    if completion:
        review_section += f"### 完成情况\n{completion}\n\n"
    if reflection:
        review_section += f"### 收获与反思\n{reflection}\n\n"
    if improvement:
        review_section += f"### 改进建议\n{improvement}\n\n"

    # 查找并替换
    if "## 🎯 今日评估" in content:
        start = content.find("## 🎯 今日评估")
        end = content.find("## 📅 明日计划", start)
        if end > start:
            content = content[:start] + review_section + content[end:]

    # 保存
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n今日评估已添加到：{file_path}")


def main():
    parser = argparse.ArgumentParser(description='总秘书每日汇总')
    parser.add_argument('--mode', choices=['summary', 'plan', 'review'],
                       default='summary', help='运行模式')
    parser.add_argument('--date', help='日期（YYYY-MM-DD），默认今天')

    args = parser.parse_args()

    # 确定日期
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # 根据模式执行
    if args.mode == 'summary':
        show_summary(date_str)
    elif args.mode == 'plan':
        add_plan(date_str)
    elif args.mode == 'review':
        add_review(date_str)


if __name__ == '__main__':
    main()
