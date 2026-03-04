#!/usr/bin/env python3
"""
每日报告生成器
整合应用追踪、工作日志、综合日志、项目数据，生成完整的每日报告
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Any
import argparse

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# 导入项目管理器
sys.path.insert(0, str(Path(__file__).parent))
from project_manager import ProjectManager

# 数据路径
WORK_TRACKER_LOG = Path.home() / "Library/Logs/work_tracker.jsonl"
SECRETARY_DIR = Path.home() / "Library/Logs/secretary"
WORK_LOG = SECRETARY_DIR / "work_log.jsonl"
PERSONAL_LOG = SECRETARY_DIR / "personal_log.jsonl"
PROJECTS_DB = SECRETARY_DIR / "projects.db"
SUMMARY_DIR = SECRETARY_DIR / "daily_summary"


def read_jsonl(file_path: Path, date_str: str = None) -> List[Dict[str, Any]]:
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


def analyze_app_usage(date_str: str) -> Dict[str, int]:
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
    sorted_usage = sorted(app_counts.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_usage)


def format_time(minutes: int) -> str:
    """格式化时间显示"""
    hours = minutes // 60
    mins = minutes % 60
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def load_secretary_logs(date_str: str) -> Dict[str, List[Dict[str, Any]]]:
    """加载工作和综合秘书日志"""
    work_logs = read_jsonl(WORK_LOG, date_str)
    personal_logs = read_jsonl(PERSONAL_LOG, date_str)

    return {
        'work': work_logs,
        'personal': personal_logs
    }


def load_project_data() -> Dict[str, List[Dict[str, Any]]]:
    """加载项目数据"""
    try:
        pm = ProjectManager(str(PROJECTS_DB))

        # 获取进行中和阻塞的项目
        in_progress = pm.list_projects(status="in_progress")
        blocked = pm.list_projects(status="blocked")

        return {
            'in_progress': in_progress,
            'blocked': blocked
        }
    except Exception as e:
        print(f"警告：无法加载项目数据：{e}", file=sys.stderr)
        return {'in_progress': [], 'blocked': []}


def build_timeline(work_logs: List[Dict], personal_logs: List[Dict], app_usage_records: List[Dict]) -> List[Dict]:
    """构建时间线（从早到晚）"""
    timeline = []

    # 添加工作日志
    for log in work_logs:
        timeline.append({
            'timestamp': log['timestamp'],
            'type': 'work',
            'content': log['content'],
            'category': log.get('category', ''),
            'tags': log.get('tags', [])
        })

    # 添加综合日志
    for log in personal_logs:
        timeline.append({
            'timestamp': log['timestamp'],
            'type': 'personal',
            'content': log['content'],
            'category': log.get('category', ''),
            'tags': log.get('tags', [])
        })

    # 按时间排序
    timeline.sort(key=lambda x: x['timestamp'])
    return timeline


def generate_report(date_str: str) -> str:
    """生成每日报告"""
    # 加载所有数据
    app_usage = analyze_app_usage(date_str)
    logs = load_secretary_logs(date_str)
    projects = load_project_data()
    app_records = read_jsonl(WORK_TRACKER_LOG, date_str)

    # 构建时间线
    timeline = build_timeline(logs['work'], logs['personal'], app_records)

    # 生成 Markdown
    lines = []
    lines.append(f"# {date_str} 工作报告\n")

    # ========== 今日概览 ==========
    lines.append("## 📊 今日概览\n")
    total_minutes = sum(app_usage.values())
    lines.append(f"- 工作时长：{format_time(total_minutes)}")
    lines.append(f"- 工作记录：{len(logs['work'])} 条")
    lines.append(f"- 综合记录：{len(logs['personal'])} 条")
    lines.append(f"- 项目进展：{len(projects['in_progress'])} 个\n")

    # ========== 时间线 ==========
    if timeline:
        lines.append("## ⏰ 时间线（从早到晚）\n")

        # 按小时分组
        by_hour = defaultdict(list)
        for item in timeline:
            ts = item['timestamp']
            if isinstance(ts, str) and 'T' in ts:
                hour = ts.split('T')[1][:2]
                by_hour[hour].append(item)

        # 按小时输出
        for hour in sorted(by_hour.keys()):
            items = by_hour[hour]
            lines.append(f"### {hour}:00")
            for item in items:
                ts = item['timestamp']
                time_str = ts.split('T')[1][:5] if 'T' in ts else ''
                content = item['content']
                tags = ' '.join(f"#{tag}" for tag in item.get('tags', []))
                icon = "💼" if item['type'] == 'work' else "🌟"
                lines.append(f"- {icon} [{time_str}] {content} {tags}")
            lines.append("")

    # ========== 应用使用统计 ==========
    if app_usage:
        lines.append("## 💻 应用使用统计\n")
        lines.append("### Top 10 应用")
        for i, (app, minutes) in enumerate(list(app_usage.items())[:10], 1):
            percentage = (minutes / total_minutes * 100) if total_minutes > 0 else 0
            lines.append(f"{i}. {app} - {format_time(minutes)} ({percentage:.1f}%)")
        lines.append("")

    # ========== 工作秘书 ==========
    lines.append("## 💼 工作秘书\n")

    # 项目进展
    if projects['in_progress'] or projects['blocked']:
        lines.append("### 项目进展")
        for project in projects['in_progress']:
            lines.append(f"**{project['name']}** (进行中)")
            if project.get('current_task'):
                lines.append(f"- 当前任务：{project['current_task']}")
            if project.get('next_steps'):
                lines.append(f"- 下一步：{project['next_steps']}")
            lines.append("")

        for project in projects['blocked']:
            lines.append(f"**{project['name']}** (阻塞)")
            if project.get('blocked_reason'):
                lines.append(f"- 阻塞原因：{project['blocked_reason']}")
            lines.append("")

    # 工作记录
    if logs['work']:
        lines.append("### 工作记录")
        for log in logs['work']:
            ts = log['timestamp']
            time_str = ts.split('T')[1][:5] if 'T' in ts else ''
            content = log['content']
            tags = ' '.join(f"#{tag}" for tag in log.get('tags', []))
            lines.append(f"- [{time_str}] {content} {tags}")
        lines.append("")

    # ========== 综合秘书 ==========
    lines.append("## 🌟 综合秘书\n")

    # 按分类分组
    by_category = defaultdict(list)
    for log in logs['personal']:
        category = log.get('category', 'other')
        by_category[category].append(log)

    # 分类映射
    category_map = {
        'investment': ('投资', '💰'),
        'stock_idea': ('投资想法', '💡'),
        'crypto': ('加密货币', '₿'),
        'macro': ('宏观经济', '📈'),
        'learning': ('学习', '📚'),
        'practice': ('实践练习', '💻'),
        'course': ('课程', '🎓'),
        'reading': ('阅读', '📖'),
        'health': ('健康', '🏃'),
        'social': ('社交', '👥'),
        'family': ('家庭', '👨‍👩‍👧'),
        'hobby': ('爱好', '🎨'),
        'todo': ('待办事项', '✅'),
        'event': ('事件', '📅'),
        'other': ('其他', '📝')
    }

    for category, (name, icon) in category_map.items():
        if category in by_category:
            lines.append(f"### {icon} {name}")
            for log in by_category[category]:
                ts = log['timestamp']
                time_str = ts.split('T')[1][:5] if 'T' in ts else ''
                content = log['content']
                tags = ' '.join(f"#{tag}" for tag in log.get('tags', []))
                lines.append(f"- [{time_str}] {content} {tags}")
            lines.append("")

    # ========== 今日评估 ==========
    lines.append("## 🎯 今日评估\n")
    lines.append("（用户手动添加）\n")

    # ========== 明日计划 ==========
    lines.append("## 📋 明日计划\n")
    lines.append("（用户手动添加）\n")

    lines.append("---\n")
    lines.append(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return '\n'.join(lines)


def save_report(date_str: str, content: str) -> Path:
    """保存报告到文件"""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
    file_path = SUMMARY_DIR / f"{date_str}.md"
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path


def main():
    parser = argparse.ArgumentParser(description='每日报告生成器')
    parser.add_argument('--date', help='日期（YYYY-MM-DD），默认今天')
    parser.add_argument('--output', help='输出文件路径（可选）')

    args = parser.parse_args()

    # 确定日期
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime('%Y-%m-%d')

    # 生成报告
    print(f"正在生成 {date_str} 的每日报告...")
    report = generate_report(date_str)

    # 保存报告
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ 报告已保存到：{output_path}")
    else:
        file_path = save_report(date_str, report)
        print(f"✅ 报告已保存到：{file_path}")

    # 显示报告
    print("\n" + "=" * 60)
    print(report)


if __name__ == '__main__':
    main()

