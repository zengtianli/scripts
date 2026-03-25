#!/usr/bin/env python3
"""
collector.py 单元测试
"""

import sys
from datetime import datetime
from pathlib import Path

# 添加 lib 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from collector import collect_conversations, collect_file_changes, collect_memory, collect_sessions


def test_collect_conversations():
    """测试对话历史采集"""
    print("测试 collect_conversations()...")

    # 测试今天的对话
    today = datetime.now().strftime("%Y-%m-%d")
    result = collect_conversations(today)

    print(f"✓ 找到 {len(result)} 个对话")

    if result:
        conv = result[0]
        assert "timestamp" in conv
        assert "topic" in conv
        assert "user_messages" in conv
        assert "assistant_messages" in conv
        assert "tools_used" in conv
        assert "files_modified" in conv
        print("✓ 对话结构正确")
        print(f"  - 主题: {conv['topic'][:30]}...")
        print(f"  - 工具: {', '.join(conv['tools_used'][:5])}")
        print(f"  - 文件: {len(conv['files_modified'])} 个")


def test_collect_file_changes():
    """测试文件变化检测"""
    print("\n测试 collect_file_changes()...")

    today = datetime.now().strftime("%Y-%m-%d")
    result = collect_file_changes(today)

    assert "modified" in result
    assert "created" in result
    assert "deleted" in result

    print("✓ 文件变化检测正常")
    print(f"  - 修改: {len(result['modified'])} 个")
    print(f"  - 创建: {len(result['created'])} 个")
    print(f"  - 删除: {len(result['deleted'])} 个")


def test_collect_sessions():
    """测试 Sessions 扫描"""
    print("\n测试 collect_sessions()...")

    today = datetime.now().strftime("%Y-%m-%d")
    result = collect_sessions(today)

    print(f"✓ 找到 {len(result)} 个 session")

    if result:
        session = result[0]
        assert "date" in session
        assert "topic" in session
        assert "summary" in session
        assert "decisions" in session
        assert "learnings" in session
        print("✓ Session 结构正确")
        print(f"  - 主题: {session['topic']}")


def test_collect_memory():
    """测试记忆读取"""
    print("\n测试 collect_memory()...")

    result = collect_memory()

    assert "core_memory" in result
    assert "user_preferences" in result
    assert "project_status" in result
    assert "system_status" in result
    assert "related_topics" in result

    print("✓ 记忆读取正常")
    print(f"  - 核心记忆: {len(result['core_memory'])} 条")
    print(f"  - 用户偏好: {len(result['user_preferences'])} 条")


if __name__ == "__main__":
    print("=" * 60)
    print("collector.py 单元测试")
    print("=" * 60)

    try:
        test_collect_conversations()
        test_collect_file_changes()
        test_collect_sessions()
        test_collect_memory()

        print("\n" + "=" * 60)
        print("✓ 所有测试通过")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
