#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title app-open
# @raycast.mode silent
# @raycast.icon 🚀
# @raycast.packageName Apps
# @raycast.description Open selected folder in specified app
# @raycast.argument1 { "type": "dropdown", "placeholder": "App", "data": [{"title": "Cursor", "value": "cursor"}, {"title": "Terminal", "value": "terminal"}, {"title": "Windsurf", "value": "windsurf"}, {"title": "Nvim", "value": "nvim"}] }

import subprocess
import os
import sys

def get_finder_selection():
    """获取 Finder 选中的文件/文件夹"""
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
    return result.stdout.strip()

def run_in_ghostty(command):
    """在 Ghostty 中运行命令"""
    applescript = f'''
    tell application "Ghostty"
        activate
        tell application "System Events"
            keystroke "n" using command down
            delay 0.3
            keystroke "{command}"
            keystroke return
        end tell
    end tell
    '''
    subprocess.run(['osascript', '-e', applescript])

def main():
    app = sys.argv[1] if len(sys.argv) > 1 else "cursor"
    path = get_finder_selection()

    if not path:
        print("❌ No folder selected")
        return

    folder_path = os.path.dirname(path) if os.path.isfile(path) else path
    name = os.path.basename(folder_path)

    if app == "cursor":
        subprocess.run(['cursor', folder_path])
        print(f"✅ Cursor opened in {name}")
    elif app == "terminal":
        subprocess.run(['open', '-a', 'Terminal', folder_path])
        print(f"✅ Terminal opened in {name}")
    elif app == "windsurf":
        subprocess.run(['windsurf', folder_path])
        print(f"✅ Windsurf opened in {name}")
    elif app == "nvim":
        command = f'cd "{folder_path}" && nvim "{path}"'
        run_in_ghostty(command)
        print(f"✅ Opened in Nvim")

if __name__ == '__main__':
    main()
