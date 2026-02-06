#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title folder-move-up-remove
# @raycast.mode fullOutput
# @raycast.icon 🗂️
# @raycast.packageName Folders
# @raycast.description 将选中文件夹内容移到上一级并删除空文件夹

import subprocess
import os
import shutil

def get_finder_selection_multiple():
    """获取 Finder 选中的多个文件"""
    script = '''
    tell application "Finder"
        set sel to selection
        set paths to {}
        repeat with f in sel
            set end of paths to POSIX path of (f as alias)
        end repeat
        set AppleScript's text item delimiters to ","
        return paths as text
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    paths = result.stdout.strip()
    if paths:
        return [p.strip().rstrip('/') for p in paths.split(',') if p.strip()]
    return []

def process_folder(folder, parent_dir, prefix="", depth=0):
    """递归处理文件夹"""
    folder_name = os.path.basename(folder)
    print(f"{prefix}📂 处理文件夹: {folder_name} (深度: {depth})")
    
    # 删除 .DS_Store
    ds_store = os.path.join(folder, '.DS_Store')
    if os.path.exists(ds_store):
        os.remove(ds_store)
        print(f"{prefix}  🧹 已删除 .DS_Store 文件")
    
    # 先递归处理子文件夹
    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)
        if os.path.isdir(item_path):
            process_folder(item_path, parent_dir, prefix + "  ", depth + 1)
    
    # 移动文件
    for item in os.listdir(folder):
        item_path = os.path.join(folder, item)
        if os.path.isfile(item_path):
            # 添加前缀避免冲突
            target_name = item if depth == 0 else f"{folder_name}_{item}"
            target_path = os.path.join(parent_dir, target_name)
            
            if os.path.exists(target_path):
                print(f"{prefix}  ⚠️ 无法移动 {item}: 目标路径已存在")
                continue
            
            try:
                shutil.move(item_path, target_path)
                print(f"{prefix}  ✓ 已移动: {item} -> {target_name}")
            except Exception as e:
                print(f"{prefix}  ❌ 移动失败: {item} ({e})")
    
    # 删除空文件夹
    try:
        remaining = os.listdir(folder)
        if not remaining:
            os.rmdir(folder)
            print(f"{prefix}  🗑️ 已删除文件夹: {folder_name}")
            return True
        else:
            print(f"{prefix}  ⚠️ 文件夹 {folder_name} 仍然不为空，无法删除")
    except Exception as e:
        print(f"{prefix}  ❌ 删除文件夹失败: {folder_name} ({e})")
    
    return False

def main():
    folders = get_finder_selection_multiple()
    
    if not folders:
        print("❌ 没有选中文件夹")
        return
    
    success_count = 0
    skipped_count = 0
    
    for folder in folders:
        if not os.path.isdir(folder):
            print(f"⚠️ 跳过 {os.path.basename(folder)} - 不是文件夹")
            skipped_count += 1
            continue
        
        parent_dir = os.path.dirname(folder)
        
        # 检查文件夹是否为空
        if not os.listdir(folder):
            print(f"  ➡️ 文件夹已经为空，直接删除")
            os.rmdir(folder)
            success_count += 1
            continue
        
        if process_folder(folder, parent_dir):
            success_count += 1
    
    print("")
    print(f"✅ 成功处理了 {success_count} 个文件夹")
    if skipped_count > 0:
        print(f"⚠️ 跳过了 {skipped_count} 个项目")

if __name__ == '__main__':
    main()

