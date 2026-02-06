#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title folder-create
# @raycast.mode fullOutput
# @raycast.icon 📁
# @raycast.packageName Folders
# @raycast.description Create a new folder inside selected folder in Finder

import subprocess
import os

def get_finder_selected_folder():
    """获取 Finder 选中的文件夹"""
    script = '''
    tell application "Finder"
        set theSelection to selection
        if (count of theSelection) > 0 then
            set firstItem to item 1 of theSelection
            if class of firstItem is folder then
                return POSIX path of (firstItem as alias)
            else
                -- 如果选中的是文件，返回其所在目录
                return POSIX path of (container of firstItem as alias)
            end if
        else
            -- 没有选中任何项目，返回当前目录
            if (count of Finder windows) > 0 then
                return POSIX path of (target of front Finder window as alias)
            else
                return POSIX path of (path to desktop folder)
            end if
        end if
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return result.stdout.strip()

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
        print("❌ 无法获取 Finder 选中的文件夹")
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
        print(f"✅ 已创建文件夹 \"{new_folder_name}\"")
    except Exception as e:
        print(f"❌ 创建文件夹失败: {e}")

if __name__ == '__main__':
    main()

