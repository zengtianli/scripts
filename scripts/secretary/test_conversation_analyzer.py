#!/usr/bin/env python3
"""
测试 conversation_analyzer.py
"""

import json
import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from conversation_analyzer import ConversationAnalyzer


def test_basic_analysis():
    """测试基本分析功能"""
    print("=== 测试基本分析 ===")
    analyzer = ConversationAnalyzer()

    # 查找今天的对话
    conversations = analyzer.find_today_conversations()
    print(f"找到 {len(conversations)} 个今天的对话记录")

    if len(conversations) == 0:
        print("警告：没有找到今天的对话记录")
        return

    # 分析第一个对话
    messages = analyzer.parse_jsonl(conversations[0])
    print(f"第一个对话包含 {len(messages)} 条消息")

    # 提取信息
    projects = analyzer.extract_projects(messages)
    print(f"提取到 {len(projects)} 个项目: {projects[:5]}")

    tasks = analyzer.extract_tasks(messages)
    print(f"提取到 {len(tasks)} 个任务")
    if tasks:
        print(f"示例任务: {tasks[0][:100]}")

    decisions = analyzer.extract_decisions(messages)
    print(f"提取到 {len(decisions)} 个决策")
    if decisions:
        print(f"示例决策: {decisions[0][:100]}")

    print()


def test_full_analysis():
    """测试完整分析"""
    print("=== 测试完整分析 ===")
    analyzer = ConversationAnalyzer()
    result = analyzer.analyze(compact=False)

    print(f"日期: {result['date']}")
    print(f"对话数: {result['conversations_count']}")
    print(f"消息数: {result['messages_count']}")
    print(f"项目数: {len(result['projects'])}")
    print(f"任务数: {len(result['tasks'])}")
    print(f"决策数: {len(result['decisions'])}")
    print(f"建议数: {len(result['suggestions'])}")

    print("\n前 3 个建议:")
    for i, suggestion in enumerate(result['suggestions'][:3], 1):
        print(f"{i}. [{suggestion['type']}] {suggestion['content'][:80]}")
        print(f"   置信度: {suggestion['confidence']}")

    print()


def test_compact_format():
    """测试压缩格式"""
    print("=== 测试压缩格式 ===")
    analyzer = ConversationAnalyzer()
    result = analyzer.analyze(compact=True)

    print(f"压缩格式输出:")
    print(json.dumps(result, ensure_ascii=False, indent=2)[:500])
    print()


def test_json_output():
    """测试 JSON 输出"""
    print("=== 测试 JSON 输出 ===")
    analyzer = ConversationAnalyzer()
    result = analyzer.analyze(compact=False)

    # 验证 JSON 可序列化
    try:
        json_str = json.dumps(result, ensure_ascii=False, indent=2)
        print(f"JSON 输出长度: {len(json_str)} 字符")
        print("JSON 序列化成功 ✓")
    except Exception as e:
        print(f"JSON 序列化失败: {e}")

    print()


def main():
    print("开始测试 conversation_analyzer.py\n")

    try:
        test_basic_analysis()
        test_full_analysis()
        test_compact_format()
        test_json_output()

        print("=== 所有测试完成 ===")

    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
