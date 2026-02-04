#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title file-copy
# @raycast.mode fullOutput
# @raycast.icon 📋
# @raycast.packageName Files
# @raycast.description Copy selected file's filename (and optionally content) to clipboard
# @raycast.argument1 { "type": "dropdown", "placeholder": "Mode", "data": [{"title": "Filename Only", "value": "name"}, {"title": "Name + Content", "value": "content"}] }

import subprocess
import os
import sys

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
    return [p.strip() for p in paths.split(',') if p.strip()] if paths else []

def copy_to_clipboard(text):
    """复制文本到剪贴板"""
    subprocess.run(['pbcopy'], input=text.encode(), check=True)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "name"
    files = get_finder_selection_multiple()

    if not files:
        print("❌ 在 Finder 中未选择文件")
        return

    if mode == "content":
        content_parts = []
        count = 0
        for file_path in files:
            filename = os.path.basename(file_path)
            if not os.path.isfile(file_path):
                print(f"⚠️ 跳过非文件: {filename}")
                continue
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                content_parts.append(f"文件名：{filename}\n\n{content}\n\n-----------------------------------\n")
                count += 1
            except Exception as e:
                print(f"⚠️ 无法读取文件: {filename} ({e})")

        if content_parts:
            copy_to_clipboard('\n'.join(content_parts))
            print(f"✅ 已复制 {count} 个文件的名称和内容到剪贴板")
        else:
            print("❌ 没有可复制的内容")
    else:
        filenames = [os.path.basename(f) for f in files]
        copy_to_clipboard('\n'.join(filenames))
        print(f"✅ 已复制 {len(filenames)} 个文件的名称到剪贴板")

if __name__ == '__main__':
    main()
