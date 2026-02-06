#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title folder-add-prefix
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Folders
# @raycast.description 将文件夹名称作为前缀添加到文件名

import subprocess
import os

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
        
        folder_name = os.path.basename(folder)
        print(f"📂 处理文件夹: {folder_name}")
        
        # 获取文件夹中的所有文件
        files = [f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))]
        
        if not files:
            print("  ⚠️ 文件夹为空，跳过")
            skipped_count += 1
            continue
        
        files_count = 0
        for filename in files:
            # 检查是否已有前缀
            if filename.startswith(folder_name):
                print(f"  ⚠️ 跳过 {filename} - 已有前缀")
                continue
            
            old_path = os.path.join(folder, filename)
            new_filename = f"{folder_name}_{filename}"
            new_path = os.path.join(folder, new_filename)
            
            try:
                os.rename(old_path, new_path)
                print(f"  ✓ 已重命名: {filename} → {new_filename}")
                files_count += 1
            except Exception as e:
                print(f"  ❌ 重命名失败: {filename} ({e})")
        
        if files_count > 0:
            print(f"✅ 共重命名了 {files_count} 个文件")
            success_count += 1
        else:
            skipped_count += 1
    
    print("")
    print(f"✅ 成功处理了 {success_count} 个文件夹")
    if skipped_count > 0:
        print(f"⚠️ 跳过了 {skipped_count} 个文件夹或空文件夹")

if __name__ == '__main__':
    main()

