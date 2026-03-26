#!/usr/bin/env python3
"""
Claude Code 对话记录分析器
分析 ~/.claude/projects/ 下的 JSONL 对话记录，提取项目、任务、决策等信息
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any


class ConversationAnalyzer:
    def __init__(self, projects_dir: str = None):
        if projects_dir is None:
            projects_dir = os.path.expanduser("~/.claude/projects")
        self.projects_dir = Path(projects_dir)

        # 关键词模式
        self.task_keywords = [
            r"创建|实现|开发|编写|修改|修复|添加|删除|重构|优化",
            r"完成|处理|解决|分析|设计|测试|部署",
        ]
        self.decision_keywords = [
            r"决定|选择|采用|使用|改为|切换到",
            r"方案|策略|架构|技术栈",
        ]
        self.project_patterns = [
            r"cursor-shared|useful_scripts|zdwp|essay|sync",
            r"~/[a-zA-Z_-]+",
        ]

    def find_today_conversations(self) -> list[Path]:
        """查找今天的对话记录文件"""
        today = datetime.now().date()
        conversations = []

        for project_dir in self.projects_dir.iterdir():
            if not project_dir.is_dir():
                continue

            for jsonl_file in project_dir.glob("*.jsonl"):
                # 检查文件修改时间
                mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime).date()
                if mtime == today:
                    conversations.append(jsonl_file)

        return conversations

    def parse_jsonl(self, file_path: Path) -> list[dict]:
        """解析 JSONL 文件"""
        messages = []
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        messages.append(data)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
        return messages

    def extract_text_from_content(self, content: Any) -> str:
        """从 message.content 提取文本"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        texts.append(item.get("text", ""))
                    elif item.get("type") == "thinking":
                        texts.append(item.get("thinking", ""))
                elif isinstance(item, str):
                    texts.append(item)
            return " ".join(texts)
        return ""

    def extract_projects(self, messages: list[dict]) -> list[str]:
        """提取项目名称"""
        projects = set()

        for msg in messages:
            # 从 cwd 提取
            cwd = msg.get("cwd", "")
            if cwd:
                # 提取目录名
                parts = cwd.split("/")
                if len(parts) > 0:
                    projects.add(parts[-1])

            # 从消息内容提取
            if "message" in msg and "content" in msg["message"]:
                text = self.extract_text_from_content(msg["message"]["content"])
                for pattern in self.project_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    projects.update(matches)

        return sorted(list(projects))

    def extract_tasks(self, messages: list[dict]) -> list[str]:
        """提取任务"""
        tasks = []

        for msg in messages:
            if msg.get("type") != "user":
                continue

            if "message" in msg and "content" in msg["message"]:
                text = self.extract_text_from_content(msg["message"]["content"])

                # 查找任务关键词
                for pattern in self.task_keywords:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        # 提取上下文（前后 50 字符）
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 80)
                        context = text[start:end].strip()
                        # 清理换行和多余空格
                        context = re.sub(r"\s+", " ", context)
                        if len(context) > 10:
                            tasks.append(context)

        return tasks[:10]  # 限制数量

    def extract_decisions(self, messages: list[dict]) -> list[str]:
        """提取决策"""
        decisions = []

        for msg in messages:
            if msg.get("type") != "assistant":
                continue

            if "message" in msg and "content" in msg["message"]:
                text = self.extract_text_from_content(msg["message"]["content"])

                # 查找决策关键词
                for pattern in self.decision_keywords:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        start = max(0, match.start() - 20)
                        end = min(len(text), match.end() + 80)
                        context = text[start:end].strip()
                        context = re.sub(r"\s+", " ", context)
                        if len(context) > 10:
                            decisions.append(context)

        return decisions[:10]

    def generate_suggestions(self, projects: list[str], tasks: list[str], decisions: list[str]) -> list[dict]:
        """生成回顾建议"""
        suggestions = []

        # 项目进展建议
        for project in projects:
            if project and len(project) > 2:
                suggestions.append(
                    {"type": "project_progress", "content": f"完成 {project} 项目相关工作", "confidence": 0.7}
                )

        # 任务建议
        for task in tasks[:5]:
            suggestions.append({"type": "work_record", "content": task, "confidence": 0.6})

        # 决策建议
        for decision in decisions[:3]:
            suggestions.append({"type": "decision", "content": decision, "confidence": 0.5})

        # 按置信度排序
        suggestions.sort(key=lambda x: x["confidence"], reverse=True)

        return suggestions[:15]

    def analyze(self, compact: bool = False) -> dict[str, Any]:
        """分析今天的对话记录"""
        conversations = self.find_today_conversations()

        all_messages = []
        for conv_file in conversations:
            messages = self.parse_jsonl(conv_file)
            all_messages.extend(messages)

        # 提取信息
        projects = self.extract_projects(all_messages)
        tasks = self.extract_tasks(all_messages)
        decisions = self.extract_decisions(all_messages)
        suggestions = self.generate_suggestions(projects, tasks, decisions)

        result = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "conversations_count": len(conversations),
            "messages_count": len(all_messages),
            "projects": projects,
            "tasks": tasks,
            "decisions": decisions,
            "suggestions": suggestions,
        }

        if compact:
            # 压缩格式：只保留建议
            result = {"date": result["date"], "suggestions": suggestions}

        return result


def main():
    import argparse

    parser = argparse.ArgumentParser(description="分析 Claude Code 对话记录")
    parser.add_argument("--compact", action="store_true", help="压缩输出格式")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--projects-dir", help="对话记录目录")

    args = parser.parse_args()

    analyzer = ConversationAnalyzer(projects_dir=args.projects_dir)
    result = analyzer.analyze(compact=args.compact)

    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"结果已保存到: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
