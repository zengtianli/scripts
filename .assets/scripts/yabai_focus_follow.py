#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title yabai-focus-follow
# @raycast.mode compact
# @raycast.icon 🎯

"""
切换 focus_follows_mouse（鼠标移到窗口就激活）
"""

import subprocess

def main():
    result = subprocess.run(['yabai', '-m', 'config', 'focus_follows_mouse'], capture_output=True, text=True)
    current = result.stdout.strip()
    
    if current in ("off", "disabled"):
        subprocess.run(['yabai', '-m', 'config', 'focus_follows_mouse', 'autofocus'])
        print("🎯 focus_follows_mouse: ON")
    else:
        subprocess.run(['yabai', '-m', 'config', 'focus_follows_mouse', 'off'])
        print("🎯 focus_follows_mouse: OFF")

if __name__ == "__main__":
    main()

