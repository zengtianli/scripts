#!/Users/tianli/miniforge3/bin/python3
"""
剪贴板操作模块
"""

import subprocess


def copy_to_clipboard(text: str):
    """复制文本到剪贴板"""
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))


def get_from_clipboard() -> str:
    """从剪贴板获取文本"""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout

