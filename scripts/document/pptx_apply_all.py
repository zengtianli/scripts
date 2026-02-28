#!/usr/bin/env python3
"""
PPT文档标准化一键处理工具
按正确顺序执行所有PPTX格式化操作

执行顺序：
1. 文本格式修复（引号、标点、单位）
2. 字体统一为微软雅黑
3. 表格样式（启用标题行、镶边行、首列）

用法:
    python3 pptx_apply_all.py <input.pptx>

示例:
    python3 pptx_apply_all.py presentation.pptx
"""

import sys
import subprocess
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from finder import get_input_files

# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).parent
PYTHON = sys.executable

# 各个处理脚本的路径
SCRIPTS = {
    'text_formatter': SCRIPT_DIR / 'pptx_text_formatter.py',
    'font_yahei': SCRIPT_DIR / 'pptx_font_yahei.py',
    'table_style': SCRIPT_DIR / 'pptx_table_style.py',
}


def show_message(msg_type, message):
    """显示格式化消息"""
    icons = {
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'info': 'ℹ️',
        'processing': '🔄'
    }
    icon = icons.get(msg_type, 'ℹ️')
    print(f"{icon} {message}")


def backup_file(file_path):
    """备份原始文件"""
    backup_path = f"{file_path}.backup"
    try:
        shutil.copy2(file_path, backup_path)
        show_message('info', f"已备份原文件: {Path(backup_path).name}")
        return backup_path
    except Exception as e:
        show_message('warning', f"备份文件失败: {e}")
        return None


def run_script(script_path, input_file, args=None):
    """
    运行指定的处理脚本

    Args:
        script_path: 脚本路径
        input_file: 输入文件
        args: 额外参数列表

    Returns:
        bool: 是否成功
    """
    cmd = [PYTHON, str(script_path), str(input_file)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False
        )

        # 打印输出
        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            if result.stderr:
                print(result.stderr)
            return False

        return True

    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False


def apply_all(input_file):
    """
    应用所有PPTX标准化处理

    Args:
        input_file: 输入文件路径
    """
    input_path = Path(input_file)

    # 检查文件是否存在
    if not input_path.exists():
        show_message('error', f"文件不存在: {input_file}")
        sys.exit(1)

    if input_path.suffix.lower() != '.pptx':
        show_message('error', "只支持 .pptx 文件")
        sys.exit(1)

    print("=" * 70)
    print("🚀 开始 PPT 文档标准化处理")
    print("=" * 70)
    print(f"📄 文件: {input_path.name}")
    print()

    # 先备份一次（后续脚本的备份会覆盖，但第一次备份是最原始的）
    backup_file(input_path)

    # 执行顺序
    steps = [
        {
            'name': '步骤 1/3: 文本格式修复',
            'script': SCRIPTS['text_formatter'],
            'args': None,
        },
        {
            'name': '步骤 2/3: 字体统一为微软雅黑',
            'script': SCRIPTS['font_yahei'],
            'args': None,
        },
        {
            'name': '步骤 3/3: 表格样式设置',
            'script': SCRIPTS['table_style'],
            'args': None,
        },
    ]

    success_count = 0
    failed_steps = []

    for step in steps:
        print("\n" + "=" * 70)
        print(f"▶️  {step['name']}")
        print("=" * 70)

        if run_script(step['script'], input_path, step['args']):
            success_count += 1
            print(f"✅ {step['name']} 完成")
        else:
            failed_steps.append(step['name'])
            print(f"⚠️ {step['name']} 失败（继续执行后续步骤）")

    # 总结
    print("\n" + "=" * 70)
    print("📊 处理总结")
    print("=" * 70)
    print(f"✅ 成功: {success_count}/{len(steps)} 个步骤")

    if failed_steps:
        print(f"⚠️ 失败: {len(failed_steps)} 个步骤")
        for step in failed_steps:
            print(f"   - {step}")
    else:
        print("🎉 所有步骤执行成功！")

    print(f"\n📄 处理完成: {input_path.name}")
    print("=" * 70)


def main():
    # 获取输入文件（优先命令行参数，否则从 Finder 获取）
    files = get_input_files(sys.argv[1:], expected_ext='pptx', allow_multiple=False)
    
    if not files:
        print("PPT文档标准化一键处理工具")
        print("\n用法: python3 pptx_apply_all.py <input.pptx>")
        print("      或在 Finder 中选择 .pptx 文件后运行")
        print("示例: python3 pptx_apply_all.py presentation.pptx")
        print("\n执行顺序:")
        print("  1. 文本格式修复（引号、标点、单位）")
        print("  2. 字体统一为微软雅黑")
        print("  3. 表格样式（启用标题行、镶边行、首列）")
        sys.exit(1)

    input_file = files[0]
    apply_all(input_file)


if __name__ == "__main__":
    main()

