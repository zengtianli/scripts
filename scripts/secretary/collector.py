#!/usr/bin/env python3
"""
数据采集器
- 对话历史读取
- 文件变化检测
- Sessions 扫描
- 记忆读取
"""

import os
import json
import sys
import re
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List
from collections import defaultdict


# 监控的关键目录
WATCH_DIRS = [
    os.path.expanduser('~/docs'),
    os.path.expanduser('~/useful_scripts'),
]

# 忽略的目录和文件
IGNORE_PATTERNS = {
    '.git', '.next', '__pycache__', '.DS_Store', 'node_modules',
    '.pnpm', '.cache', '.venv', 'dist', 'build', '.pytest_cache',
    '.mypy_cache', '.ruff_cache', '.turbo', '.idea', '.vscode',
    '*.pyc', '*.pyo', '.env', '.env.local'
}


def should_ignore(path: str) -> bool:
    """检查路径是否应该被忽略"""
    parts = Path(path).parts
    for part in parts:
        if part in IGNORE_PATTERNS:
            return True
        # 检查文件扩展名
        if part.endswith('.pyc') or part.endswith('.pyo'):
            return True
    return False


def get_file_changes_for_date(target_date: date) -> Dict[str, List[str]]:
    """
    检测指定日期的文件变化

    Args:
        target_date: 目标日期 (date 对象或 'YYYY-MM-DD' 字符串)

    Returns:
        {
            "modified": ["file1.md", "file2.py"],
            "created": ["file3.md"],
            "deleted": ["file4.md"]
        }
    """
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

    modified_files = []
    created_files = []
    deleted_files = []

    # 定义日期范围（整个目标日期）
    date_start = datetime.combine(target_date, datetime.min.time()).timestamp()
    date_end = datetime.combine(target_date, datetime.max.time()).timestamp()

    # 扫描所有监控目录
    for watch_dir in WATCH_DIRS:
        if not os.path.exists(watch_dir):
            continue

        for root, dirs, files in os.walk(watch_dir):
            # 原地修改 dirs 列表以跳过忽略的目录
            dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]

            for filename in files:
                if should_ignore(filename):
                    continue

                filepath = os.path.join(root, filename)

                try:
                    stat_info = os.stat(filepath)
                    mtime = stat_info.st_mtime
                    ctime = stat_info.st_ctime

                    # 检查文件是否在目标日期修改
                    if date_start <= mtime <= date_end:
                        # 相对路径（从 watch_dir 开始）
                        rel_path = os.path.relpath(filepath, watch_dir)

                        # 判断是创建还是修改
                        # 如果 ctime 和 mtime 接近（差异小于 1 秒），认为是新建
                        if abs(ctime - mtime) < 1:
                            created_files.append(rel_path)
                        else:
                            modified_files.append(rel_path)

                except (OSError, ValueError):
                    # 跳过无法访问的文件
                    continue

    # 排序文件列表
    modified_files.sort()
    created_files.sort()
    deleted_files.sort()

    return {
        "modified": modified_files,
        "created": created_files,
        "deleted": deleted_files
    }


def collect_file_changes(date: str) -> Dict:
    """
    检测指定日期的文件变化

    Args:
        date: 日期字符串 (YYYY-MM-DD 格式)

    Returns:
        {
            "modified": ["file1.md", "file2.py"],
            "created": ["file3.md"],
            "deleted": ["file4.md"]
        }
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"日期格式不正确，应为 YYYY-MM-DD，收到: {date}")

    return get_file_changes_for_date(target_date)


def _extract_markdown_section(content: str, section_title: str) -> str:
    """
    从 Markdown 内容中提取指定章节的内容

    Args:
        content: Markdown 文件内容
        section_title: 章节标题（如 "## 一、任务概述"）

    Returns:
        章节内容（不包括标题）
    """
    lines = content.split('\n')
    start_idx = -1
    end_idx = len(lines)

    # 找到章节开始
    for i, line in enumerate(lines):
        if section_title in line:
            start_idx = i + 1
            break

    if start_idx == -1:
        return ""

    # 找到下一个同级或更高级的标题
    for i in range(start_idx, len(lines)):
        line = lines[i]
        # 检查是否是同级或更高级的标题
        if line.startswith('## ') or line.startswith('# '):
            end_idx = i
            break

    return '\n'.join(lines[start_idx:end_idx]).strip()


def _extract_list_items(content: str, max_items: int = 10) -> List[str]:
    """
    从 Markdown 内容中提取列表项

    Args:
        content: Markdown 内容
        max_items: 最多提取的项数

    Returns:
        列表项列表
    """
    items = []
    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        # 匹配 - 或 * 或 数字. 开头的列表项
        if line.startswith('- ') or line.startswith('* ') or (len(line) > 2 and line[0].isdigit() and line[1:3] == '. '):
            # 移除列表标记
            if line.startswith('- '):
                item = line[2:].strip()
            elif line.startswith('* '):
                item = line[2:].strip()
            else:
                item = line.split('. ', 1)[1].strip()

            # 移除 Markdown 格式（✅、❌ 等）
            item = item.lstrip('✅❌📋📊🎉✨🔧📝')
            item = item.strip()

            if item:
                items.append(item)
                if len(items) >= max_items:
                    break

    return items


def collect_sessions(date: str) -> List[Dict]:
    """
    扫描指定日期的工作会话

    Args:
        date: 日期字符串 (YYYY-MM-DD 格式)

    Returns:
        [{
            "date": "2026-03-02",
            "topic": "raycast规范化",
            "summary": "完成报告内容...",
            "decisions": ["决策1", "决策2"],
            "learnings": ["学习1", "学习2"]
        }]
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"日期格式不正确，应为 YYYY-MM-DD，收到: {date}")

    # 构建 sessions 目录路径
    year_month = target_date.strftime('%Y-%m')
    sessions_dir = os.path.expanduser(f'~/docs/sessions/{year_month}')

    if not os.path.exists(sessions_dir):
        return []

    results = []
    day_str = target_date.strftime('%d')

    # 扫描目录
    try:
        entries = os.listdir(sessions_dir)
    except OSError:
        return []

    for entry in sorted(entries):
        entry_path = os.path.join(sessions_dir, entry)

        # 检查是否是目录且以日期开头
        if not os.path.isdir(entry_path) or not entry.startswith(day_str):
            continue

        # 提取 topic（去掉日期前缀，如 "02-" → "raycast规范化"）
        topic = entry
        if '-' in topic:
            parts = topic.split('-', 1)
            if len(parts) > 1:
                topic = parts[1]

        # 读取完成报告
        report_path = os.path.join(entry_path, '完成报告.md')
        summary = ""
        decisions = []
        learnings = []

        if os.path.exists(report_path):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    report_content = f.read()

                # 提取摘要（从标题到第一个主要章节）
                lines = report_content.split('\n')
                summary_lines = []
                in_header = True
                for line in lines:
                    # 跳过标题和分隔线
                    if line.startswith('#') or line.startswith('---') or line.startswith('**'):
                        in_header = False
                        continue
                    # 当遇到主要章节时停止
                    if line.startswith('## '):
                        break
                    # 收集非空行
                    if line.strip() and not in_header:
                        summary_lines.append(line.strip())
                        if len(summary_lines) >= 3:  # 最多 3 行
                            break

                summary = ' '.join(summary_lines)[:200]  # 限制长度

                # 提取决策（从"执行内容"或"建立的规范体系"章节）
                decisions_section = _extract_markdown_section(report_content, '## 二、')
                if not decisions_section:
                    decisions_section = _extract_markdown_section(report_content, '## 三、')

                if decisions_section:
                    decisions = _extract_list_items(decisions_section, max_items=5)

                # 提取学习（从"核心改进"或"后续维护"章节）
                learnings_section = _extract_markdown_section(report_content, '## 六、')
                if not learnings_section:
                    learnings_section = _extract_markdown_section(report_content, '## 五、')

                if learnings_section:
                    learnings = _extract_list_items(learnings_section, max_items=5)

            except (OSError, UnicodeDecodeError):
                pass

        # 构建结果
        session_data = {
            "date": date,
            "topic": topic,
            "summary": summary,
            "decisions": decisions,
            "learnings": learnings
        }

        results.append(session_data)

    return results


# ============================================================================
# 对话历史采集
# ============================================================================

def collect_conversations(date: str) -> List[Dict]:
    """
    读取指定日期的 Claude Code 对话历史（增强版）

    参数：
        date: "2026-03-02" 格式的日期字符串

    返回：
        对话列表，每个对话包含详细的 session 信息：
        - session_id: 会话 ID
        - time_range: 时间范围（开始、结束、持续时间）
        - topic: 对话主题
        - conversation: 完整对话记录（包含每条消息的详细信息）
        - iterations: 迭代过程（问题-解决循环）
        - file_operations: 文件操作统计
        - file_changes_by_dir: 按目录分组的文件变更
        - summary: 会话摘要统计
        - context: 任务背景（如果有）
        - pitfalls: 踩的坑（如果有）
        - lessons: 经验教训（如果有）
    """
    target_date = datetime.strptime(date, '%Y-%m-%d').date()
    conversations = _load_conversations_by_date(target_date)
    return _format_conversations_enhanced(conversations, date)


def _read_jsonl_incremental(filepath: Path):
    """增量读取 JSONL 文件，逐行解析"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # 跳过无效的 JSON 行
                    continue
    except (OSError, UnicodeDecodeError):
        # 跳过无法读取的文件
        pass


def _load_conversations_by_date(target_date: date) -> Dict[str, List[Dict]]:
    """按日期加载对话，按 sessionId 分组"""
    projects_dir = Path.home() / ".claude" / "projects" / "-Users-tianli"
    conversations = defaultdict(list)

    for jsonl_file in projects_dir.glob("*.jsonl"):
        for entry in _read_jsonl_incremental(jsonl_file):
            # 解析时间戳
            timestamp_str = entry.get('timestamp')
            if not timestamp_str:
                continue

            try:
                entry_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                entry_date = entry_time.date()
            except (ValueError, AttributeError):
                continue

            # 过滤日期
            if entry_date != target_date:
                continue

            # 只保留 user 和 assistant 类型的消息
            msg_type = entry.get('type')
            if msg_type not in ('user', 'assistant'):
                continue

            session_id = entry.get('sessionId', 'unknown')
            conversations[session_id].append(entry)

    return conversations


def _format_conversations(conversations: Dict[str, List[Dict]]) -> List[Dict]:
    """格式化对话数据（简化版，保留向后兼容）"""
    results = []

    for session_id, entries in conversations.items():
        if not entries:
            continue

        # 按时间排序
        entries.sort(key=lambda x: x.get('timestamp', ''))

        # 提取信息
        user_messages = []
        assistant_messages = []
        tools_used = set()
        files_modified = set()

        for entry in entries:
            msg_type = entry.get('type')
            message = entry.get('message', {})
            content = message.get('content', '')

            if msg_type == 'user':
                user_messages.append(_clean_message(content))
            elif msg_type == 'assistant':
                assistant_messages.append(_clean_message(content))
                # 提取工具使用
                tools = _extract_tools_from_message(message)
                tools_used.update(tools)
                # 提取文件修改
                files = _extract_files_from_message(message)
                files_modified.update(files)

        # 推断主题
        topic = _extract_topic(entries)

        # 获取开始时间
        timestamp = entries[0].get('timestamp', '')

        results.append({
            'timestamp': timestamp,
            'topic': topic,
            'user_messages': user_messages,
            'assistant_messages': assistant_messages,
            'tools_used': sorted(list(tools_used)),
            'files_modified': sorted(list(files_modified))
        })

    # 按时间排序
    results.sort(key=lambda x: x['timestamp'])
    return results


def _format_conversations_enhanced(conversations: Dict[str, List[Dict]], date: str = None) -> List[Dict]:
    """格式化对话数据（增强版）"""
    results = []

    for session_id, entries in conversations.items():
        if not entries:
            continue

        # 按时间排序
        entries.sort(key=lambda x: x.get('timestamp', ''))

        # 分析 session 详情（传递日期参数）
        session_details = analyze_session_details(session_id, entries, date)
        results.append(session_details)

    # 按时间排序
    results.sort(key=lambda x: x['time_range']['start'])
    return results


def collect_session_docs(date: str, topic: str) -> Dict:
    """
    从 sessions 目录读取完成报告

    参数：
        date: 日期字符串 (YYYY-MM-DD)
        topic: 会话主题（用于匹配目录名）

    返回：
        {
            'doc_path': '完成报告路径',
            'content': '完整内容',
            'context': {...},
            'pitfalls': [...],
            'lessons': [...]
        }
    """
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
    except ValueError:
        return {}

    # 构建 sessions 目录路径
    year_month = target_date.strftime('%Y-%m')
    sessions_dir = os.path.expanduser(f'~/docs/sessions/{year_month}')

    if not os.path.exists(sessions_dir):
        return {}

    # 查找匹配的 session 目录
    day_str = target_date.strftime('%d')
    matching_dirs = []

    try:
        entries = os.listdir(sessions_dir)
    except OSError:
        return {}

    for entry in entries:
        entry_path = os.path.join(sessions_dir, entry)
        if os.path.isdir(entry_path) and entry.startswith(day_str):
            # 检查主题是否匹配（模糊匹配）
            topic_clean = topic[:30].lower()  # 取前30个字符
            entry_clean = entry.lower()
            if any(word in entry_clean for word in topic_clean.split()[:3]):
                matching_dirs.append(entry_path)

    # 如果没有匹配，返回空
    if not matching_dirs:
        return {}

    # 读取第一个匹配的完成报告
    for session_dir in matching_dirs:
        report_path = os.path.join(session_dir, '完成报告.md')
        if os.path.exists(report_path):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                return {
                    'doc_path': report_path,
                    'content': content,
                    'context': _extract_context_from_doc(content),
                    'pitfalls': _extract_pitfalls_from_doc(content),
                    'lessons': _extract_lessons_from_doc(content)
                }
            except (OSError, UnicodeDecodeError):
                continue

    return {}


def _extract_context_from_doc(content: str) -> Dict:
    """
    从完成报告中提取 context（出发点、问题、为什么）

    参数：
        content: 完成报告内容

    返回：
        {
            'trigger': '触发原因',
            'problem': '要解决的问题',
            'why': '为什么要做'
        }
    """
    context = {
        'trigger': '',
        'problem': '',
        'why': ''
    }

    # 提取"任务概述"章节
    overview_section = _extract_markdown_section(content, '## 一、任务概述')
    if not overview_section:
        overview_section = _extract_markdown_section(content, '## 任务概述')

    if overview_section:
        lines = overview_section.split('\n')
        # 第一段通常是触发原因和问题描述
        paragraphs = []
        current_para = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
            elif not line.startswith('#') and not line.startswith('-') and not line.startswith('*'):
                current_para.append(line)

        if current_para:
            paragraphs.append(' '.join(current_para))

        # 第一段作为 trigger
        if paragraphs:
            context['trigger'] = paragraphs[0][:200]

    # 提取"以前的问题"或"问题"章节
    problems_section = _extract_markdown_section(content, '**以前的问题**')
    if not problems_section:
        problems_section = _extract_markdown_section(content, '### 问题')

    if problems_section:
        items = _extract_list_items(problems_section, max_items=3)
        if items:
            context['problem'] = '; '.join(items)

    # 提取"核心目标"或"为什么"
    goals_section = _extract_markdown_section(content, '### 核心目标')
    if not goals_section:
        goals_section = _extract_markdown_section(content, '### 为什么')

    if goals_section:
        items = _extract_list_items(goals_section, max_items=3)
        if items:
            context['why'] = '; '.join(items)

    return context


def _extract_pitfalls_from_doc(content: str) -> List[str]:
    """
    从完成报告中提取 pitfalls（踩的坑）

    参数：
        content: 完成报告内容

    返回：
        踩坑列表
    """
    pitfalls = []

    # 查找"以前的问题"章节（只提取到下一个 ** 标记）
    if '**以前的问题**' in content:
        start_idx = content.index('**以前的问题**')
        # 查找下一个 ** 标记
        next_section_idx = content.find('**', start_idx + len('**以前的问题**'))
        if next_section_idx > start_idx:
            problems_text = content[start_idx:next_section_idx]
        else:
            problems_text = content[start_idx:start_idx+500]  # 最多500字符

        items = _extract_list_items(problems_text, max_items=10)
        pitfalls.extend(items)

    # 查找"踩坑记录"章节
    pitfalls_section = _extract_markdown_section(content, '### 踩坑记录')
    if not pitfalls_section:
        pitfalls_section = _extract_markdown_section(content, '## 踩坑')

    if pitfalls_section:
        items = _extract_list_items(pitfalls_section, max_items=10)
        pitfalls.extend(items)

    # 去重
    unique_pitfalls = []
    seen = set()
    for p in pitfalls:
        p_lower = p.lower()
        if p_lower not in seen:
            seen.add(p_lower)
            unique_pitfalls.append(p)

    return unique_pitfalls[:10]  # 最多返回10个


def _extract_lessons_from_doc(content: str) -> List[str]:
    """
    从完成报告中提取 lessons（经验教训）

    参数：
        content: 完成报告内容

    返回：
        经验教训列表
    """
    lessons = []

    # 查找"现在的解决方案"章节（只提取到下一个 ** 或 ## 标记）
    if '**现在的解决方案**' in content:
        start_idx = content.index('**现在的解决方案**')
        # 查找下一个 ** 或 ## 标记
        next_section_idx = len(content)
        for marker in ['**', '\n##']:
            idx = content.find(marker, start_idx + len('**现在的解决方案**'))
            if idx > start_idx and idx < next_section_idx:
                next_section_idx = idx

        solutions_text = content[start_idx:next_section_idx]
        items = _extract_list_items(solutions_text, max_items=10)
        lessons.extend(items)

    # 查找"经验教训"章节
    lessons_section = _extract_markdown_section(content, '### 经验教训')
    if not lessons_section:
        lessons_section = _extract_markdown_section(content, '## 经验教训')

    if lessons_section:
        items = _extract_list_items(lessons_section, max_items=10)
        lessons.extend(items)

    # 去重
    unique_lessons = []
    seen = set()
    for l in lessons:
        l_lower = l.lower()
        if l_lower not in seen:
            seen.add(l_lower)
            unique_lessons.append(l)

    return unique_lessons[:10]  # 最多返回10个


def _extract_pitfalls_from_conversation(entries: List[Dict]) -> List[str]:
    """
    从对话历史中识别错误和纠正

    参数：
        entries: 会话中的所有消息条目

    返回：
        识别出的错误列表
    """
    pitfalls = []

    # 识别关键词
    error_keywords = ['错了', '不对', '有问题', '怎么回事', '不应该', '不是', '别', '不要']
    correction_keywords = ['抱歉', '对不起', '我错了', '修正', '更正', '重新']

    for i, entry in enumerate(entries):
        msg_type = entry.get('type')
        message = entry.get('message', {})
        content = _extract_text_content(message.get('content', ''))

        # 检查用户的批评/纠正
        if msg_type == 'user':
            for keyword in error_keywords:
                if keyword in content:
                    # 提取这条消息作为 pitfall
                    pitfall = content[:100]  # 限制长度
                    if pitfall and pitfall not in pitfalls:
                        pitfalls.append(pitfall)
                    break

        # 检查助手的错误承认
        elif msg_type == 'assistant':
            for keyword in correction_keywords:
                if keyword in content:
                    # 查找前一条用户消息
                    if i > 0:
                        prev_entry = entries[i-1]
                        if prev_entry.get('type') == 'user':
                            prev_content = _extract_text_content(prev_entry.get('message', {}).get('content', ''))
                            pitfall = prev_content[:100]
                            if pitfall and pitfall not in pitfalls:
                                pitfalls.append(pitfall)
                    break

    return pitfalls[:5]  # 最多返回5个


def analyze_session_details(session_id: str, entries: List[Dict], date: str = None) -> Dict:
    """
    分析单个 session 的详细信息

    参数：
        session_id: 会话 ID
        entries: 会话中的所有消息条目
        date: 日期字符串（用于查找 session 文档）

    返回：
        详细的 session 分析结果
    """
    if not entries:
        return {}

    # 1. 提取时间范围
    timestamps = [e.get('timestamp') for e in entries if e.get('timestamp')]
    time_range = _extract_time_range(timestamps)

    # 2. 提取完整对话
    conversation = _extract_full_conversation(entries)

    # 3. 识别迭代过程
    iterations = _identify_iterations(entries)

    # 4. 统计文件操作
    file_operations = _extract_file_operations(entries)

    # 5. 按目录分组文件变更
    file_changes_by_dir = _group_files_by_directory(file_operations)

    # 6. 推断主题
    topic = _extract_topic(entries)

    # 7. 生成摘要统计
    summary = _generate_session_summary(entries, conversation, file_operations)

    # 8. 从 session 文档提取 context/pitfalls/lessons
    session_doc = {}
    if date:
        session_doc = collect_session_docs(date, topic)

    # 9. 从对话中识别 pitfalls
    conversation_pitfalls = _extract_pitfalls_from_conversation(entries)

    # 10. 合并 context/pitfalls/lessons
    context = session_doc.get('context', {})
    pitfalls = session_doc.get('pitfalls', []) + conversation_pitfalls
    lessons = session_doc.get('lessons', [])

    # 去重
    pitfalls = list(dict.fromkeys(pitfalls))[:10]
    lessons = list(dict.fromkeys(lessons))[:10]

    result = {
        'session_id': session_id,
        'time_range': time_range,
        'topic': topic,
        'conversation': conversation,
        'iterations': iterations,
        'file_operations': file_operations,
        'file_changes_by_dir': file_changes_by_dir,
        'summary': summary
    }

    # 只在有内容时添加这些字段
    if context and any(context.values()):
        result['context'] = context

    if pitfalls:
        result['pitfalls'] = pitfalls

    if lessons:
        result['lessons'] = lessons

    return result


def _extract_time_range(timestamps: List[str]) -> Dict:
    """提取时间范围"""
    if not timestamps:
        return {
            'start': None,
            'end': None,
            'duration_minutes': 0
        }

    # 解析时间戳
    parsed_times = []
    for ts in timestamps:
        try:
            dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
            parsed_times.append(dt)
        except (ValueError, AttributeError):
            continue

    if not parsed_times:
        return {
            'start': None,
            'end': None,
            'duration_minutes': 0
        }

    start_time = min(parsed_times)
    end_time = max(parsed_times)
    duration = (end_time - start_time).total_seconds() / 60

    return {
        'start': start_time.isoformat(),
        'end': end_time.isoformat(),
        'duration_minutes': round(duration, 1)
    }


def _extract_full_conversation(entries: List[Dict]) -> List[Dict]:
    """提取完整对话记录 - 优化版（过滤空消息）"""
    conversation = []

    for entry in entries:
        msg_type = entry.get('type')
        if msg_type not in ('user', 'assistant'):
            continue

        message = entry.get('message', {})
        content = message.get('content', '')
        timestamp = entry.get('timestamp', '')
        message_id = entry.get('uuid', '')

        # 提取文本内容
        content_text = _extract_text_content(content)

        # 构建消息记录
        msg_record = {
            'timestamp': timestamp,
            'role': msg_type,
            'message_id': message_id
        }

        if msg_type == 'user':
            # 用户消息：只保留有内容的
            if not content_text:
                continue
            msg_record['content'] = content_text

        elif msg_type == 'assistant':
            # 助手消息：提取文本、工具使用、文件操作
            tools_used = _extract_tools_from_message(message)
            files_affected = _extract_files_from_message(message)

            # 只保留有内容或有工具使用的消息
            if not content_text and not tools_used:
                continue

            msg_record['content'] = content_text
            msg_record['tools_used'] = tools_used
            msg_record['files_affected'] = files_affected

        conversation.append(msg_record)

    return conversation


def _extract_text_content(content) -> str:
    """从消息内容中提取纯文本"""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
                elif block.get('type') == 'thinking':
                    # 可选：包含思考内容
                    pass
            elif isinstance(block, str):
                text_parts.append(block)
        return ' '.join(text_parts).strip()

    return str(content).strip()


def _identify_iterations(entries: List[Dict]) -> List[Dict]:
    """识别迭代过程（问题-解决循环）- 优化版"""
    iterations = []
    current_iteration = None
    iteration_count = 0

    for entry in entries:
        msg_type = entry.get('type')
        message = entry.get('message', {})
        content_text = _extract_text_content(message.get('content', ''))

        if msg_type == 'user':
            # 只有当用户消息有实际内容时，才开始新的迭代
            if not content_text:
                continue

            # 保存上一个迭代（如果有内容）
            if current_iteration and (current_iteration['user_request'] or
                                     current_iteration['assistant_response'] or
                                     current_iteration['tools_used']):
                iterations.append(current_iteration)

            iteration_count += 1
            current_iteration = {
                'round': iteration_count,
                'user_request': content_text,
                'assistant_response': '',
                'tools_used': [],
                'files_affected': []
            }

        elif msg_type == 'assistant' and current_iteration:
            # 收集助手的响应内容
            if content_text and not current_iteration['assistant_response']:
                current_iteration['assistant_response'] = content_text

            # 收集工具使用
            tools = _extract_tools_from_message(message)
            for tool in tools:
                if tool not in current_iteration['tools_used']:
                    current_iteration['tools_used'].append(tool)

            # 收集受影响的文件
            files = _extract_files_from_message(message)
            for file in files:
                if file not in current_iteration['files_affected']:
                    current_iteration['files_affected'].append(file)

    # 添加最后一个迭代（如果有内容）
    if current_iteration and (current_iteration['user_request'] or
                             current_iteration['assistant_response'] or
                             current_iteration['tools_used']):
        iterations.append(current_iteration)

    return iterations


def _extract_file_operations(entries: List[Dict]) -> Dict:
    """提取文件操作统计"""
    operations = {
        'read': [],
        'write': [],
        'edit': [],
        'glob': [],
        'grep': []
    }

    for entry in entries:
        if entry.get('type') != 'assistant':
            continue

        message = entry.get('message', {})
        content = message.get('content', [])

        if not isinstance(content, list):
            continue

        for block in content:
            if not isinstance(block, dict) or block.get('type') != 'tool_use':
                continue

            tool_name = block.get('name', '')
            input_data = block.get('input', {})

            if tool_name == 'Read':
                file_path = input_data.get('file_path')
                if file_path:
                    operations['read'].append(file_path)

            elif tool_name == 'Write':
                file_path = input_data.get('file_path')
                if file_path:
                    operations['write'].append(file_path)

            elif tool_name == 'Edit':
                file_path = input_data.get('file_path')
                if file_path:
                    operations['edit'].append(file_path)

            elif tool_name == 'Glob':
                pattern = input_data.get('pattern')
                if pattern:
                    operations['glob'].append(pattern)

            elif tool_name == 'Grep':
                pattern = input_data.get('pattern')
                if pattern:
                    operations['grep'].append(pattern)

    # 去重并排序
    for key in operations:
        operations[key] = sorted(list(set(operations[key])))

    return operations


def _group_files_by_directory(file_operations: Dict) -> Dict:
    """
    按目录分组文件变更

    参数：
        file_operations: 文件操作字典（包含 write, edit 等）

    返回：
        按目录分组的文件变更：
        {
            "~/cursor-shared/.oa/": {
                "created": ["app/api/secretary/daily/route.ts"],
                "modified": ["app/secretary/page.tsx"],
                "deleted": []
            }
        }
    """
    from pathlib import Path

    dir_groups = {}

    # 处理 write（新建文件）
    for file_path in file_operations.get('write', []):
        if not file_path:
            continue

        # 提取目录和文件名
        path_obj = Path(file_path)

        # 获取目录路径（相对于 home 目录）
        try:
            home = Path.home()
            if path_obj.is_absolute() and path_obj.is_relative_to(home):
                # 转换为 ~/ 格式
                rel_path = path_obj.relative_to(home)
                dir_path = f"~/{rel_path.parent}/"
                file_name = rel_path.name
            else:
                # 使用绝对路径
                dir_path = f"{path_obj.parent}/"
                file_name = path_obj.name
        except (ValueError, AttributeError):
            # 如果无法处理，使用原始路径
            dir_path = f"{path_obj.parent}/"
            file_name = path_obj.name

        # 初始化目录组
        if dir_path not in dir_groups:
            dir_groups[dir_path] = {
                'created': [],
                'modified': [],
                'deleted': []
            }

        # 添加到 created 列表
        if file_name not in dir_groups[dir_path]['created']:
            dir_groups[dir_path]['created'].append(file_name)

    # 处理 edit（修改文件）
    for file_path in file_operations.get('edit', []):
        if not file_path:
            continue

        path_obj = Path(file_path)

        try:
            home = Path.home()
            if path_obj.is_absolute() and path_obj.is_relative_to(home):
                rel_path = path_obj.relative_to(home)
                dir_path = f"~/{rel_path.parent}/"
                file_name = rel_path.name
            else:
                dir_path = f"{path_obj.parent}/"
                file_name = path_obj.name
        except (ValueError, AttributeError):
            dir_path = f"{path_obj.parent}/"
            file_name = path_obj.name

        if dir_path not in dir_groups:
            dir_groups[dir_path] = {
                'created': [],
                'modified': [],
                'deleted': []
            }

        # 添加到 modified 列表（如果不在 created 中）
        if file_name not in dir_groups[dir_path]['created'] and file_name not in dir_groups[dir_path]['modified']:
            dir_groups[dir_path]['modified'].append(file_name)

    # 排序每个目录的文件列表
    for dir_path in dir_groups:
        dir_groups[dir_path]['created'].sort()
        dir_groups[dir_path]['modified'].sort()
        dir_groups[dir_path]['deleted'].sort()

    # 按目录路径排序
    return dict(sorted(dir_groups.items()))


def _generate_session_summary(entries: List[Dict], conversation: List[Dict], file_operations: Dict) -> Dict:
    """生成会话摘要统计"""
    user_count = sum(1 for e in entries if e.get('type') == 'user')
    assistant_count = sum(1 for e in entries if e.get('type') == 'assistant')

    # 统计工具使用
    tools_used = {}
    for entry in entries:
        if entry.get('type') != 'assistant':
            continue
        message = entry.get('message', {})
        for tool in _extract_tools_from_message(message):
            tools_used[tool] = tools_used.get(tool, 0) + 1

    # 统计受影响的文件
    all_files = set()
    for op_list in file_operations.values():
        all_files.update(op_list)

    return {
        'total_messages': len(entries),
        'user_messages': user_count,
        'assistant_messages': assistant_count,
        'tools_used': tools_used,
        'files_affected_count': len(all_files),
        'files_affected': sorted(list(all_files))
    }


def _clean_message(content: str) -> str:
    """清理消息内容，移除噪音"""
    if not content:
        return ""

    # 如果是列表，提取文本内容
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    text_parts.append(block.get('text', ''))
            elif isinstance(block, str):
                text_parts.append(block)
        content = ' '.join(text_parts)

    # 如果不是字符串，转换为字符串
    if not isinstance(content, str):
        content = str(content)

    # 限制长度
    max_length = 500
    if len(content) > max_length:
        content = content[:max_length] + "..."

    return content.strip()


def _extract_topic(entries: List[Dict]) -> str:
    """从对话中提取主题"""
    # 从第一条 user 消息提取
    for entry in entries:
        if entry.get('type') == 'user':
            message = entry.get('message', {})
            content = message.get('content', '')

            # 移除 teammate-message 标签
            if '<teammate-message' in content:
                # 提取标签内的内容
                match = re.search(r'<teammate-message[^>]*>(.*?)</teammate-message>', content, re.DOTALL)
                if match:
                    content = match.group(1)

            # 取前 50 个字符作为主题
            topic = content.strip()[:50]
            if len(content) > 50:
                topic += "..."
            return topic

    return "未知主题"


def _extract_tools_from_message(message: Dict) -> List[str]:
    """从 assistant 消息中提取使用的工具"""
    tools = []
    content = message.get('content', '')

    if not isinstance(content, list):
        return tools

    # content 可能是列表，包含 tool_use 块
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'tool_use':
            tool_name = block.get('name')
            if tool_name:
                tools.append(tool_name)

    return tools


def _extract_files_from_message(message: Dict) -> List[str]:
    """从 assistant 消息中提取修改的文件"""
    files = []
    content = message.get('content', '')

    if not isinstance(content, list):
        return files

    # 查找 Edit, Write 工具的 file_path 参数
    for block in content:
        if isinstance(block, dict) and block.get('type') == 'tool_use':
            tool_name = block.get('name')
            if tool_name in ('Edit', 'Write', 'NotebookEdit'):
                input_data = block.get('input', {})
                file_path = input_data.get('file_path') or input_data.get('notebook_path')
                if file_path:
                    files.append(file_path)

    return files


def collect_memory() -> Dict:
    """
    读取 Claude Code 记忆

    返回：
        {
            "core_memory": [...],
            "user_preferences": [...],
            "project_status": {...},
            "system_status": {...},
            "related_topics": [...]
        }
    """
    memory_path = os.path.expanduser('~/.claude/projects/-Users-tianli/memory/MEMORY.md')

    if not os.path.exists(memory_path):
        return {
            'core_memory': [],
            'user_preferences': [],
            'project_status': {},
            'system_status': {},
            'related_topics': [],
        }

    try:
        with open(memory_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return {
            'core_memory': [],
            'user_preferences': [],
            'project_status': {},
            'system_status': {},
            'related_topics': [],
        }

    result = {
        'core_memory': [],
        'user_preferences': [],
        'project_status': {},
        'system_status': {},
        'related_topics': [],
    }

    # 解析 Markdown 结构
    lines = content.split('\n')
    current_section = None
    current_subsection = None
    current_content = []

    for line in lines:
        # 一级标题
        if line.startswith('# '):
            if current_section and current_content:
                section_text = '\n'.join(current_content).strip()
                if current_section == '核心记忆':
                    result['core_memory'].append({
                        'title': current_subsection or '核心记忆',
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    })
                elif current_section == '用户偏好':
                    result['user_preferences'].append({
                        'title': current_subsection or '用户偏好',
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    })
                elif current_section == '项目状态':
                    if current_subsection:
                        result['project_status'][current_subsection] = {
                            'content': section_text,
                            'items': _extract_list_items(section_text),
                        }
                elif current_section == '系统状态':
                    if current_subsection:
                        result['system_status'][current_subsection] = {
                            'content': section_text,
                            'items': _extract_list_items(section_text),
                        }
                elif current_section == '相关主题文件':
                    result['related_topics'].append({
                        'title': current_subsection or '相关主题文件',
                        'items': _extract_list_items(section_text),
                    })

                current_content = []

            current_section = line[2:].strip()
            current_subsection = None

        # 二级标题
        elif line.startswith('## '):
            if current_subsection and current_content:
                section_text = '\n'.join(current_content).strip()
                if current_section == '核心记忆':
                    result['core_memory'].append({
                        'title': current_subsection,
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    })
                elif current_section == '用户偏好':
                    result['user_preferences'].append({
                        'title': current_subsection,
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    })
                elif current_section == '项目状态':
                    result['project_status'][current_subsection] = {
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    }
                elif current_section == '系统状态':
                    result['system_status'][current_subsection] = {
                        'content': section_text,
                        'items': _extract_list_items(section_text),
                    }
                elif current_section == '相关主题文件':
                    result['related_topics'].append({
                        'title': current_subsection,
                        'items': _extract_list_items(section_text),
                    })

                current_content = []

            current_subsection = line[3:].strip()

        # 内容行
        elif line.strip():
            current_content.append(line)

    # 处理最后一个部分
    if current_section and current_content:
        section_text = '\n'.join(current_content).strip()
        if current_section == '核心记忆':
            result['core_memory'].append({
                'title': current_subsection or '核心记忆',
                'content': section_text,
                'items': _extract_list_items(section_text),
            })
        elif current_section == '用户偏好':
            result['user_preferences'].append({
                'title': current_subsection or '用户偏好',
                'content': section_text,
                'items': _extract_list_items(section_text),
            })
        elif current_section == '项目状态':
            if current_subsection:
                result['project_status'][current_subsection] = {
                    'content': section_text,
                    'items': _extract_list_items(section_text),
                }
        elif current_section == '系统状态':
            if current_subsection:
                result['system_status'][current_subsection] = {
                    'content': section_text,
                    'items': _extract_list_items(section_text),
                }
        elif current_section == '相关主题文件':
            result['related_topics'].append({
                'title': current_subsection or '相关主题文件',
                'items': _extract_list_items(section_text),
            })

    return result


def analyze_daily_data(collected_data: Dict) -> Dict:
    """
    智能分析今天的数据

    Args:
        collected_data: 包含 conversations, sessions, file_changes, memory 的字典

    Returns:
        分析结果，包含 overview, works, decisions, learnings
    """
    conversations = collected_data.get('conversations', [])
    sessions = collected_data.get('sessions', [])
    file_changes = collected_data.get('file_changes', {})

    # 计算统计信息
    total_files_changed = (
        len(file_changes.get('modified', [])) +
        len(file_changes.get('created', [])) +
        len(file_changes.get('deleted', []))
    )

    # 估算工作时长（基于对话和会话）
    estimated_hours = len(conversations) * 0.5 + len(sessions) * 1.0

    overview = {
        'work_hours': round(estimated_hours, 1),
        'tasks_count': len(sessions),
        'files_changed': total_files_changed,
        'conversations': len(conversations)
    }

    # 提取工作内容（按项目分类）
    works = []
    for session in sessions:
        work_item = {
            'project': session.get('topic', '未知项目'),
            'tasks': session.get('decisions', [])[:3],  # 取前3个决策作为任务
            'time': f"{len(session.get('decisions', [])) + len(session.get('learnings', []))}h"
        }
        works.append(work_item)

    # 提取决策
    decisions = []
    for session in sessions:
        for decision in session.get('decisions', []):
            decisions.append(decision)

    # 提取学习
    learnings = []
    for session in sessions:
        for learning in session.get('learnings', []):
            learnings.append(learning)

    return {
        'overview': overview,
        'works': works,
        'decisions': decisions,
        'learnings': learnings
    }


def main():
    """主函数"""
    date = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime('%Y-%m-%d')

    try:
        # 采集增强版对话数据（包含 context/pitfalls/lessons）
        sessions = collect_conversations(date)

        # 获取文件变更
        file_changes = get_file_changes_for_date(date)

        # 计算统计信息
        total_files_changed = (
            len(file_changes.get('modified', [])) +
            len(file_changes.get('created', [])) +
            len(file_changes.get('deleted', []))
        )

        # 计算工作时长（基于 sessions 的实际时间）
        total_minutes = sum(s.get('time_range', {}).get('duration_minutes', 0) for s in sessions)
        work_hours = round(total_minutes / 60, 1)

        # 构建概览
        overview = {
            'work_hours': work_hours,
            'tasks_count': len(sessions),
            'files_changed': total_files_changed,
            'conversations': len(sessions)
        }

        # 构建最终结果
        result = {
            "date": date,
            "overview": overview,
            "sessions": sessions
        }

        # 输出 JSON
        print(json.dumps(result, ensure_ascii=False, indent=2))

    except ValueError as e:
        print(f'错误: {e}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'未知错误: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

