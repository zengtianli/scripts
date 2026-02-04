#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title yabai-mouse-follow
# @raycast.mode compact
# @raycast.icon 🖱️

"""
切换 mouse_follows_focus（键盘切窗口时鼠标跟过去）
"""

import subprocess

def main():
    result = subprocess.run(['yabai', '-m', 'config', 'mouse_follows_focus'], capture_output=True, text=True)
    current = result.stdout.strip()
    
    if current == "off":
        subprocess.run(['yabai', '-m', 'config', 'mouse_follows_focus', 'on'])
        print("🖱️ mouse_follows_focus: ON")
    else:
        subprocess.run(['yabai', '-m', 'config', 'mouse_follows_focus', 'off'])
        print("🖱️ mouse_follows_focus: OFF")

if __name__ == "__main__":
    main()
