#!/usr/bin/env python3
"""
file_tracker.py 测试脚本
"""

import json
import os
import sys
import tempfile
from datetime import date, datetime, timedelta

# 添加脚本目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from file_tracker import FileTracker


def test_basic_tracking():
    """测试基本追踪功能"""
    print("测试 1: 基本追踪功能")
    print("-" * 50)

    tracker = FileTracker()
    tracker.track_all()
    tracker.sort_files()

    result = tracker.to_dict()

    print(f"追踪日期: {result['date']}")
    print(f"Work 文件数: {result['summary']['work_count']}")
    print(f"Personal 文件数: {result['summary']['personal_count']}")
    print(f"总计: {result['summary']['total_count']}")

    if result["work_files"]:
        print("\n最近修改的 Work 文件:")
        for f in result["work_files"][-3:]:
            print(f"  - {f['path']} ({f['time']})")

    if result["personal_files"]:
        print("\n最近修改的 Personal 文件:")
        for f in result["personal_files"][-3:]:
            print(f"  - {f['path']} ({f['time']})")

    print()
    return result


def test_json_output():
    """测试 JSON 输出"""
    print("测试 2: JSON 输出格式")
    print("-" * 50)

    tracker = FileTracker()
    tracker.track_all()
    tracker.sort_files()

    json_str = tracker.to_json()
    data = json.loads(json_str)

    print("JSON 结构验证:")
    print(f"  ✓ 包含 date 字段: {bool(data.get('date'))}")
    print(f"  ✓ 包含 work_files 字段: {bool('work_files' in data)}")
    print(f"  ✓ 包含 personal_files 字段: {bool('personal_files' in data)}")
    print(f"  ✓ 包含 summary 字段: {bool('summary' in data)}")

    if data["work_files"]:
        sample = data["work_files"][0]
        print("\n  Work 文件样本字段:")
        print(f"    - path: {bool('path' in sample)}")
        print(f"    - action: {bool('action' in sample)}")
        print(f"    - time: {bool('time' in sample)}")
        print(f"    - size: {bool('size' in sample)}")

    print()


def test_ignore_patterns():
    """测试忽略模式"""
    print("测试 3: 忽略模式")
    print("-" * 50)

    tracker = FileTracker()

    test_cases = [
        ("/path/to/.git/config", True),
        ("/path/to/__pycache__/module.pyc", True),
        ("/path/to/node_modules/package/index.js", True),
        ("/path/to/.DS_Store", True),
        ("/path/to/normal_file.py", False),
        ("/path/to/src/main.py", False),
    ]

    for path, should_ignore in test_cases:
        result = tracker.should_ignore(path)
        status = "✓" if result == should_ignore else "✗"
        print(f"  {status} {path}: {result}")

    print()


def test_timestamp_formatting():
    """测试时间戳格式化"""
    print("测试 4: 时间戳格式化")
    print("-" * 50)

    tracker = FileTracker()

    # 测试当前时间
    now = datetime.now().timestamp()
    formatted = tracker.format_timestamp(now)

    print(f"当前时间戳: {now}")
    print(f"格式化结果: {formatted}")
    print(f"格式验证: {bool('T' in formatted and ':' in formatted)}")

    print()


def test_date_filtering():
    """测试日期过滤"""
    print("测试 5: 日期过滤")
    print("-" * 50)

    # 测试不同日期
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)

    tracker_today = FileTracker(today)
    tracker_yesterday = FileTracker(yesterday)
    tracker_tomorrow = FileTracker(tomorrow)

    print(f"今天 ({today}): 追踪中...")
    tracker_today.track_all()
    print(f"  找到 {len(tracker_today.work_files) + len(tracker_today.personal_files)} 个文件")

    print(f"昨天 ({yesterday}): 追踪中...")
    tracker_yesterday.track_all()
    print(f"  找到 {len(tracker_yesterday.work_files) + len(tracker_yesterday.personal_files)} 个文件")

    print(f"明天 ({tomorrow}): 追踪中...")
    tracker_tomorrow.track_all()
    print(f"  找到 {len(tracker_tomorrow.work_files) + len(tracker_tomorrow.personal_files)} 个文件")

    print()


def test_with_temp_files():
    """测试临时文件追踪"""
    print("测试 6: 临时文件追踪")
    print("-" * 50)

    # 创建临时目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建测试文件
        test_file = os.path.join(tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # 获取文件信息
        stat_info = os.stat(test_file)
        mtime = stat_info.st_mtime
        file_date = datetime.fromtimestamp(mtime).date()

        print(f"创建测试文件: {test_file}")
        print(f"修改时间: {datetime.fromtimestamp(mtime)}")
        print(f"文件日期: {file_date}")
        print(f"今天日期: {date.today()}")
        print(f"日期匹配: {file_date == date.today()}")

    print()


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("文件追踪器测试套件")
    print("=" * 50 + "\n")

    try:
        test_basic_tracking()
        test_json_output()
        test_ignore_patterns()
        test_timestamp_formatting()
        test_date_filtering()
        test_with_temp_files()

        print("=" * 50)
        print("✓ 所有测试完成")
        print("=" * 50)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
