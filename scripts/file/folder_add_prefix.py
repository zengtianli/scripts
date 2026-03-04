#!/usr/bin/env python3

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from finder import get_input_files
from display import show_success, show_error, show_info

def main():
    folders = get_input_files([], allow_multiple=True)

    if not folders:
        return
    
    success_count = 0
    skipped_count = 0

    for folder in folders:
        folder = folder.rstrip('/')
        if not os.path.isdir(folder):
            show_info(f"跳过 {os.path.basename(folder)} - 不是文件夹")
            skipped_count += 1
            continue

        folder_name = os.path.basename(folder)
        show_info(f"处理文件夹: {folder_name}")

        # 获取文件夹中的所有文件
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]

        if not files:
            show_info("  文件夹为空，跳过")
            skipped_count += 1
            continue

        files_count = 0
        for filename in files:
            # 检查是否已有前缀
            if filename.startswith(folder_name):
                show_info(f"  跳过 {filename} - 已有前缀")
                continue

            old_path = os.path.join(folder, filename)
            new_filename = f"{folder_name}_{filename}"
            new_path = os.path.join(folder, new_filename)

            try:
                os.rename(old_path, new_path)
                show_info(f"  已重命名: {filename} → {new_filename}")
                files_count += 1
            except Exception as e:
                show_error(f"  重命名失败: {filename} ({e})")

        if files_count > 0:
            show_info(f"共重命名了 {files_count} 个文件")
            success_count += 1
        else:
            skipped_count += 1

    show_success(f"成功处理了 {success_count} 个文件夹")
    if skipped_count > 0:
        show_info(f"跳过了 {skipped_count} 个文件夹或空文件夹")

if __name__ == '__main__':
    main()

