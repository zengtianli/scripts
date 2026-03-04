#!/usr/bin/env python3
"""秘书系统 - 每日回顾（采集 → 分析 → 报告）"""

import sys
from datetime import datetime
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("📝 秘书系统 - 每日回顾\n")

    # 第 1 步：采集今天的数据
    print("="*50)
    print("第 1 步：采集数据")
    print("="*50 + "\n")

    try:
        from collector import get_file_changes_for_date
        from datetime import date

        today = date.today()
        changes = get_file_changes_for_date(today)

        print(f"📊 今天的文件变化：")
        print(f"  - 新建文件：{len(changes.get('created', []))} 个")
        print(f"  - 修改文件：{len(changes.get('modified', []))} 个")
        print(f"  - 删除文件：{len(changes.get('deleted', []))} 个")

        if changes.get('modified'):
            print(f"\n  修改的文件：")
            for f in changes['modified'][:5]:
                print(f"    - {f}")
            if len(changes['modified']) > 5:
                print(f"    ... 还有 {len(changes['modified']) - 5} 个文件")
    except Exception as e:
        print(f"⚠️  采集数据失败：{e}")

    # 第 2 步：分析数据
    print("\n" + "="*50)
    print("第 2 步：分析数据")
    print("="*50 + "\n")

    try:
        from conversation_analyzer import ConversationAnalyzer

        analyzer = ConversationAnalyzer()
        conversations = analyzer.find_today_conversations()

        print(f"💬 今天的对话记录：")
        print(f"  - 对话文件：{len(conversations)} 个")

        if conversations:
            for conv_file in conversations[:3]:
                print(f"    - {conv_file.name}")
            if len(conversations) > 3:
                print(f"    ... 还有 {len(conversations) - 3} 个文件")
    except Exception as e:
        print(f"⚠️  分析数据失败：{e}")

    # 第 3 步：生成报告
    print("\n" + "="*50)
    print("第 3 步：生成报告")
    print("="*50 + "\n")

    try:
        from daily_report import generate_report

        today_str = datetime.now().strftime('%Y-%m-%d')
        print(f"📄 生成 {today_str} 的每日报告...\n")
        generate_report(today_str)
    except Exception as e:
        print(f"⚠️  生成报告失败：{e}")

    print("\n✅ 每日回顾完成！")


if __name__ == "__main__":
    main()
