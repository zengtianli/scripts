#!/usr/bin/env python3
"""
每日回顾生成器 - 智能生成回顾选项
整合项目数据库、对话记录分析、文件系统变化
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 导入项目管理器
sys.path.insert(0, str(Path(__file__).parent))
from project_manager import ProjectManager

# 日志文件路径
WORK_LOG = Path.home() / "Library" / "Logs" / "secretary" / "work_log.jsonl"
PERSONAL_LOG = Path.home() / "Library" / "Logs" / "secretary" / "personal_log.jsonl"

# 分类映射
WORK_CATEGORIES = {
    "1": "project_progress",
    "2": "meeting",
    "3": "task",
    "4": "code_review",
    "5": "documentation",
    "6": "bug_fix",
    "7": "deployment",
    "8": "planning"
}

PERSONAL_CATEGORIES = {
    "1": "investment",
    "2": "learning",
    "3": "health",
    "4": "social",
    "5": "family",
    "6": "hobby",
    "7": "reading",
    "8": "other"
}

PRIORITIES = {
    "1": "high",
    "2": "medium",
    "3": "low"
}


class ReviewSuggestion:
    """回顾建议"""
    def __init__(
        self,
        content: str,
        category_type: str,  # 'work' or 'personal'
        confidence: float = 1.0,
        source: str = "project_db",
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.content = content
        self.category_type = category_type
        self.confidence = confidence
        self.source = source
        self.metadata = metadata or {}


def get_suggestions_from_projects() -> List[ReviewSuggestion]:
    """从项目数据库获取建议"""
    suggestions = []

    try:
        pm = ProjectManager()
        in_progress_projects = pm.list_projects(status="in_progress")

        for project in in_progress_projects:
            # 构建回顾内容
            content = f"{project['name']}"
            if project.get('current_task'):
                content += f" - {project['current_task']}"

            # 确定分类类型
            category_type = project['type']  # 'work' or 'personal'

            # 构建元数据
            metadata = {
                'project_id': project['id'],
                'project_name': project['name'],
                'priority': project.get('priority', 'medium'),
                'tags': project.get('tags', [])
            }

            suggestions.append(ReviewSuggestion(
                content=content,
                category_type=category_type,
                confidence=1.0,
                source="project_db",
                metadata=metadata
            ))

    except Exception as e:
        print(f"⚠️  获取项目数据失败: {e}")

    return suggestions


def get_suggestions_from_conversations() -> List[ReviewSuggestion]:
    """从对话记录分析获取建议"""
    import subprocess

    suggestions = []

    try:
        # 调用 conversation_analyzer.py
        script_path = Path(__file__).parent / "conversation_analyzer.py"
        result = subprocess.run(
            [sys.executable, str(script_path), "--compact"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"⚠️  对话分析失败: {result.stderr}")
            return []

        # 解析 JSON 输出
        data = json.loads(result.stdout)

        # 转换为 ReviewSuggestion
        for suggestion in data.get("suggestions", []):
            content = suggestion.get("content", "")
            confidence = suggestion.get("confidence", 0.5)
            suggestion_type = suggestion.get("type", "work_record")

            # 根据类型判断分类
            category_type = "work"  # 对话记录主要是工作相关

            suggestions.append(ReviewSuggestion(
                content=content,
                category_type=category_type,
                confidence=confidence,
                source="conversation",
                metadata={"suggestion_type": suggestion_type}
            ))

    except subprocess.TimeoutExpired:
        print("⚠️  对话分析超时")
    except json.JSONDecodeError as e:
        print(f"⚠️  解析对话分析结果失败: {e}")
    except Exception as e:
        print(f"⚠️  获取对话分析失败: {e}")

    return suggestions


def get_suggestions_from_files() -> List[ReviewSuggestion]:
    """从文件系统变化获取建议"""
    import subprocess

    suggestions = []

    try:
        # 调用 file_tracker.py
        script_path = Path(__file__).parent / "file_tracker.py"
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"⚠️  文件追踪失败: {result.stderr}")
            return []

        # 解析 JSON 输出
        data = json.loads(result.stdout)

        # 从工作文件生成建议
        work_files = data.get("work_files", [])
        if work_files:
            # 按目录分组
            dir_groups = {}
            for file_info in work_files:
                file_path = file_info.get("path", "")
                dir_name = Path(file_path).parent.name
                if dir_name not in dir_groups:
                    dir_groups[dir_name] = []
                dir_groups[dir_name].append(file_info)

            # 为每个目录生成建议
            for dir_name, files in list(dir_groups.items())[:5]:  # 限制数量
                file_count = len(files)
                content = f"修改了 {dir_name} 目录下的 {file_count} 个文件"

                suggestions.append(ReviewSuggestion(
                    content=content,
                    category_type="work",
                    confidence=0.6,
                    source="file_system",
                    metadata={"dir": dir_name, "file_count": file_count}
                ))

        # 从个人文件生成建议
        personal_files = data.get("personal_files", [])
        if personal_files:
            dir_groups = {}
            for file_info in personal_files:
                file_path = file_info.get("path", "")
                dir_name = Path(file_path).parent.name
                if dir_name not in dir_groups:
                    dir_groups[dir_name] = []
                dir_groups[dir_name].append(file_info)

            for dir_name, files in list(dir_groups.items())[:5]:
                file_count = len(files)
                content = f"更新了 {dir_name} 相关内容（{file_count} 个文件）"

                suggestions.append(ReviewSuggestion(
                    content=content,
                    category_type="personal",
                    confidence=0.6,
                    source="file_system",
                    metadata={"dir": dir_name, "file_count": file_count}
                ))

    except subprocess.TimeoutExpired:
        print("⚠️  文件追踪超时")
    except json.JSONDecodeError as e:
        print(f"⚠️  解析文件追踪结果失败: {e}")
    except Exception as e:
        print(f"⚠️  获取文件追踪失败: {e}")

    return suggestions


def get_all_suggestions() -> List[ReviewSuggestion]:
    """整合所有数据源的建议"""
    suggestions = []

    # 从项目数据库获取
    suggestions.extend(get_suggestions_from_projects())

    # 从对话记录获取（预留）
    suggestions.extend(get_suggestions_from_conversations())

    # 从文件系统获取（预留）
    suggestions.extend(get_suggestions_from_files())

    # 按置信度排序
    suggestions.sort(key=lambda x: x.confidence, reverse=True)

    return suggestions


def get_input(prompt: str, default: Optional[str] = None) -> str:
    """获取用户输入"""
    if default:
        prompt = f"{prompt} [{default}]"
    value = input(f"{prompt}: ").strip()
    return value if value else (default or "")


def display_suggestions(suggestions: List[ReviewSuggestion]):
    """显示建议列表"""
    print("\n📋 建议的回顾内容：")
    for i, suggestion in enumerate(suggestions, 1):
        category_label = "work" if suggestion.category_type == "work" else "personal"
        print(f"  {i}. [{category_label}] {suggestion.content}")
    print(f"  {len(suggestions) + 1}. [添加新内容]")


def select_suggestions(suggestions: List[ReviewSuggestion]) -> List[ReviewSuggestion]:
    """让用户选择要记录的建议"""
    selection = get_input("\n请选择要记录的内容（输入序号，逗号分隔）", "")

    if not selection:
        return []

    selected = []
    indices = [s.strip() for s in selection.split(",")]

    for idx_str in indices:
        try:
            idx = int(idx_str)
            if 1 <= idx <= len(suggestions):
                selected.append(suggestions[idx - 1])
            elif idx == len(suggestions) + 1:
                # 添加新内容
                selected.append(None)  # None 表示需要手动输入
        except ValueError:
            print(f"⚠️  无效的序号: {idx_str}")

    return selected


def process_suggestion(suggestion: Optional[ReviewSuggestion], index: int) -> Optional[Dict[str, Any]]:
    """处理单个建议，返回日志条目"""
    print(f"\n--- 内容 {index} ---")

    # 获取内容
    if suggestion is None:
        content = get_input("记录内容")
        if not content:
            print("❌ 内容不能为空，跳过")
            return None
        category_type = None
        metadata = {}
    else:
        content = get_input("记录内容", suggestion.content)
        category_type = suggestion.category_type
        metadata = suggestion.metadata.copy()

    # 确定分类类型（work/personal）
    if category_type is None:
        print("\n类型选择：")
        print("  1. work")
        print("  2. personal")
        type_key = get_input("选择类型", "1")
        category_type = "work" if type_key == "1" else "personal"

    # 获取具体分类
    categories = WORK_CATEGORIES if category_type == "work" else PERSONAL_CATEGORIES
    print(f"\n分类选择（{category_type}）：")
    for key, value in categories.items():
        print(f"  {key}. {value}")

    default_category = "1"
    category_key = get_input("选择分类", default_category)
    category = categories.get(category_key, list(categories.values())[0])

    # 获取优先级
    print("\n优先级：")
    for key, value in PRIORITIES.items():
        print(f"  {key}. {value}")

    default_priority = "2"
    if 'priority' in metadata:
        priority_map = {"high": "1", "medium": "2", "low": "3"}
        default_priority = priority_map.get(metadata['priority'], "2")

    priority_key = get_input("选择优先级", default_priority)
    priority = PRIORITIES.get(priority_key, "medium")

    # 获取标签
    default_tags = ", ".join(metadata.get('tags', []))
    tags_input = get_input("标签（逗号分隔）", default_tags)
    tags = [tag.strip() for tag in tags_input.split(",") if tag.strip()]

    # 获取项目 ID（如果是工作类型）
    project_id = metadata.get('project_id', '')
    if category_type == "work":
        project_id = get_input("项目 ID（可选）", project_id)
        if project_id:
            metadata['project_id'] = project_id

    # 构建日志条目
    log_entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "secretary": category_type,
        "category": category,
        "content": content,
        "tags": tags,
        "priority": priority,
        "metadata": metadata
    }

    return log_entry, category_type


def save_log_entry(log_entry: Dict[str, Any], category_type: str):
    """保存日志条目"""
    log_file = WORK_LOG if category_type == "work" else PERSONAL_LOG

    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 追加到日志文件
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


def main():
    print("🌟 每日回顾生成器\n")

    # 获取所有建议
    suggestions = get_all_suggestions()

    if not suggestions:
        print("📝 没有找到建议，请手动输入回顾内容")
        suggestions = []

    # 显示建议
    display_suggestions(suggestions)

    # 让用户选择
    selected = select_suggestions(suggestions)

    if not selected:
        print("\n❌ 未选择任何内容")
        sys.exit(0)

    # 处理每个选择
    saved_count = 0
    for i, suggestion in enumerate(selected, 1):
        result = process_suggestion(suggestion, i)
        if result:
            log_entry, category_type = result
            save_log_entry(log_entry, category_type)
            saved_count += 1

    print(f"\n✅ 已保存 {saved_count} 条回顾记录")


if __name__ == "__main__":
    main()
