#!/usr/bin/env python3
"""
脚本功能描述

用途：简要说明脚本的主要功能
使用：通过 Raycast 调用或直接运行
"""

# ============================================================
# 路径设置 - 引用公共库
# ============================================================
from pathlib import Path
import sys

# 将 lib/ 目录添加到 Python 路径
# 注意：scripts/ 下的脚本使用此路径设置
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

# ============================================================
# 导入标准库
# ============================================================
import os
import subprocess
from typing import Optional, List

# ============================================================
# 导入公共库（根据需要选择）
# ============================================================
# from finder import get_finder_selection  # Finder 操作
# from file_ops import safe_read, safe_write  # 文件操作
# from excel_ops import read_excel, write_excel  # Excel 操作
# from core.docx_core import DocxProcessor  # Word 文档处理
# from core.xlsx_core import XlsxProcessor  # Excel 处理
# from hydraulic import get_encoding_map  # 水利领域专用

# ============================================================
# 工具函数
# ============================================================

def get_finder_selection() -> Optional[str]:
    """
    获取 Finder 选中的文件/文件夹

    Returns:
        str: 文件路径，如果没有选中则返回 None
    """
    script = '''
    tell application "Finder"
        if (count of Finder windows) > 0 then
            set sel to selection
            if (count of sel) > 0 then
                return POSIX path of (item 1 of sel as alias)
            else
                return POSIX path of (target of front Finder window as alias)
            end if
        else
            return ""
        end if
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    path = result.stdout.strip()
    return path if path else None


def show_notification(title: str, message: str):
    """
    显示 macOS 通知

    Args:
        title: 通知标题
        message: 通知内容
    """
    script = f'''
    display notification "{message}" with title "{title}"
    '''
    subprocess.run(['osascript', '-e', script])


def validate_file(file_path: str, expected_ext: str = None) -> bool:
    """
    验证文件是否存在且扩展名正确

    Args:
        file_path: 文件路径
        expected_ext: 期望的扩展名（如 '.py', '.txt'）

    Returns:
        bool: 验证是否通过
    """
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return False

    if not os.path.isfile(file_path):
        print(f"❌ 不是文件: {file_path}")
        return False

    if expected_ext:
        _, ext = os.path.splitext(file_path)
        if ext.lower() != expected_ext.lower():
            print(f"❌ 文件扩展名错误: 期望 {expected_ext}, 实际 {ext}")
            return False

    return True


# ============================================================
# 主要功能函数
# ============================================================

def process_file(file_path: str) -> bool:
    """
    处理文件的主要逻辑

    Args:
        file_path: 要处理的文件路径

    Returns:
        bool: 处理是否成功
    """
    try:
        # TODO: 实现具体的处理逻辑
        print(f"🔄 正在处理: {os.path.basename(file_path)}")

        # 示例：读取文件
        # with open(file_path, 'r', encoding='utf-8') as f:
        #     content = f.read()

        # 示例：处理内容
        # processed_content = content.upper()

        # 示例：写入结果
        # output_path = file_path.replace('.txt', '_processed.txt')
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     f.write(processed_content)

        print(f"✅ 处理完成")
        return True

    except Exception as e:
        print(f"❌ 处理失败: {str(e)}")
        return False


# ============================================================
# 主函数
# ============================================================

def main():
    """主函数 - 脚本入口"""

    # 方式1：从命令行参数获取文件路径
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    # 方式2：从 Finder 获取选中的文件
    else:
        file_path = get_finder_selection()
        if not file_path:
            print("❌ 未选中文件")
            return

    # 验证文件
    # if not validate_file(file_path, expected_ext='.txt'):
    #     return

    # 处理文件
    success = process_file(file_path)

    # 显示通知（可选）
    if success:
        show_notification("处理完成", f"已处理: {os.path.basename(file_path)}")
    else:
        show_notification("处理失败", "请查看终端输出")


if __name__ == '__main__':
    main()
