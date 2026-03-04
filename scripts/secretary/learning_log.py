#!/usr/bin/env python3
"""
学习秘书 - 记录学习笔记
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# 日志文件路径
LOG_FILE = Path.home() / "Library" / "Logs" / "secretary" / "learning_log.jsonl"

# 分类选项
CATEGORIES = {
    "1": "reading",      # 阅读
    "2": "course",       # 课程
    "3": "practice",     # 实践
    "4": "insight",      # 灵感
    "5": "paper"         # 论文
}

# 优先级选项
PRIORITIES = {
    "1": "high",
    "2": "medium",
    "3": "low"
}


def ensure_log_dir():
    """确保日志目录存在"""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def get_input(prompt, default=None):
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]"
    value = input(f"{prompt}: ").strip()
    return value if value else default


def select_option(options, prompt):
    """选择选项"""
    print(f"\n{prompt}:")
    for key, value in options.items():
        print(f"  {key}. {value}")
    choice = input("选择: ").strip()
    return options.get(choice, list(options.values())[0])


def main():
    print("=== 学习秘书 - 记录学习笔记 ===\n")

    # 获取学习内容
    content = get_input("学习内容")
    if not content:
        print("错误：学习内容不能为空")
        sys.exit(1)

    # 选择分类
    category = select_option(CATEGORIES, "选择分类")

    # 获取标签
    tags_input = get_input("标签（逗号分隔）", "")
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

    # 选择优先级
    priority = select_option(PRIORITIES, "选择优先级")

    # 获取扩展信息
    metadata = {}

    if category == "reading":
        book = get_input("书名（可选）", "")
        if book:
            metadata["book"] = book
        chapter_input = get_input("章节（可选）", "")
        if chapter_input:
            try:
                metadata["chapter"] = int(chapter_input)
            except ValueError:
                metadata["chapter"] = chapter_input
        progress = get_input("进度（可选，如 30%）", "")
        if progress:
            metadata["progress"] = progress

    elif category == "course":
        course = get_input("课程名称（可选）", "")
        if course:
            metadata["course"] = course
        progress = get_input("进度（可选，如 50%）", "")
        if progress:
            metadata["progress"] = progress

    elif category == "practice":
        project = get_input("项目名称（可选）", "")
        if project:
            metadata["project"] = project

    # 构建日志条目
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "category": category,
        "content": content,
        "tags": tags,
        "priority": priority,
        "metadata": metadata
    }

    # 写入日志文件
    ensure_log_dir()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    print("\n✅ 学习笔记已记录！")
    print(f"分类: {category}")
    print(f"优先级: {priority}")
    if tags:
        print(f"标签: {', '.join(tags)}")


if __name__ == "__main__":
    main()
