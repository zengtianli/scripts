#!/usr/bin/env python3
"""
ZDWP Word文档标准化一键处理工具
按正确顺序执行所有ZDWP格式化操作

执行顺序：
1. 文本格式修复（引号、标点、单位、m2/m3上标）
2. 自动识别并应用标题样式（标题1-4）
3. 应用正文样式（ZDWP正文）
4. 应用表格样式（ZDWP表格内容+表名+表头加粗+实线边框+表格后空行）
5. 应用图片和图名样式（ZDWP图名+图片题注后空行）
6. 数字和英文字母字体格式化（Times New Roman）

用法:
    python3 apply_zdwp_all.py <input.docx>

示例:
    python3 apply_zdwp_all.py document.docx
"""

import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from finder import get_input_files

# 获取当前脚本所在目录
SCRIPT_DIR = Path(__file__).parent
PYTHON = sys.executable

# 各个处理脚本的路径
SCRIPTS = {
    'text_formatter': SCRIPT_DIR / 'docx_text_formatter.py',
    'heading_styles': SCRIPT_DIR / 'docx_apply_heading_styles.py',
    'paragraph_style': SCRIPT_DIR / 'docx_apply_paragraph_style.py',
    'table_style': SCRIPT_DIR / 'docx_apply_table_style.py',
    'image_caption': SCRIPT_DIR / 'docx_apply_image_caption.py',
    'numbers_font': SCRIPT_DIR / 'docx_format_numbers_font.py',
}

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

def apply_zdwp_all(input_file):
    """
    应用所有ZDWP标准化处理

    Args:
        input_file: 输入文件路径
    """
    input_path = Path(input_file)

    # 检查文件是否存在
    if not input_path.exists():
        print(f"❌ 错误: 文件不存在: {input_file}")
        sys.exit(1)

    if input_path.suffix.lower() != '.docx':
        print(f"❌ 错误: 只支持 .docx 文件")
        sys.exit(1)

    print("=" * 70)
    print("🚀 开始 ZDWP 文档标准化处理")
    print("=" * 70)
    print(f"📄 文件: {input_path.name}")
    print()

    # 执行顺序
    steps = [
        {
            'name': '步骤 1/6: 文本格式修复',
            'script': SCRIPTS['text_formatter'],
            'args': None,
        },
        {
            'name': '步骤 2/6: 自动识别标题',
            'script': SCRIPTS['heading_styles'],
            'args': None,
        },
        {
            'name': '步骤 3/6: 应用正文样式',
            'script': SCRIPTS['paragraph_style'],
            'args': ['ZDWP正文'],
        },
        {
            'name': '步骤 4/6: 应用表格样式',
            'script': SCRIPTS['table_style'],
            'args': ['ZDWP表格内容'],
        },
        {
            'name': '步骤 5/6: 应用图片和图名样式',
            'script': SCRIPTS['image_caption'],
            'args': ['ZDWP图名'],
        },
        {
            'name': '步骤 6/6: 字体格式化',
            'script': SCRIPTS['numbers_font'],
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
    files = get_input_files(sys.argv[1:], expected_ext='docx', allow_multiple=False)
    
    if not files:
        print("ZDWP Word文档标准化一键处理工具")
        print("\n用法: python3 apply_zdwp_all.py <input.docx>")
        print("      或在 Finder 中选择 .docx 文件后运行")
        print("示例: python3 apply_zdwp_all.py document.docx")
        print("\n执行顺序:")
        print("  1. 文本格式修复（引号、标点、单位、m2/m3上标）")
        print("  2. 自动识别并应用标题样式（标题1-4）")
        print("  3. 应用正文样式（ZDWP正文）")
        print("  4. 应用表格样式（ZDWP表格内容+表名+表头加粗+实线边框+表格后空行）")
        print("  5. 应用图片和图名样式（ZDWP图名+图片题注后空行）")
        print("  6. 数字和英文字母字体格式化（Times New Roman）")
        sys.exit(1)

    input_file = files[0]
    apply_zdwp_all(input_file)

if __name__ == "__main__":
    main()

