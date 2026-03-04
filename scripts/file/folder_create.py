#!/usr/bin/env python3

import subprocess
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from finder import get_finder_selected_folder
from display import show_success, show_error

def select_in_finder(path):
    """在 Finder 中选中文件/文件夹"""
    script = f'''
    tell application "Finder"
        activate
        select POSIX file "{path}"
    end tell
    '''
    subprocess.run(['osascript', '-e', script])

def main():
    target_dir = get_finder_selected_folder()

    if not target_dir:
        show_error("无法获取 Finder 选中的文件夹")
        return

    # 设置默认文件夹名称
    base_name = "untitled folder"
    new_folder_name = base_name
    counter = 2

    # 如果文件夹已存在，自动添加序号
    while os.path.exists(os.path.join(target_dir, new_folder_name)):
        new_folder_name = f"{base_name} {counter}"
        counter += 1

    new_folder_path = os.path.join(target_dir, new_folder_name)

    try:
        os.makedirs(new_folder_path)
        select_in_finder(new_folder_path)
        show_success(f"已创建文件夹 \"{new_folder_name}\"")
    except Exception as e:
        show_error(f"创建文件夹失败: {e}")

if __name__ == '__main__':
    main()

