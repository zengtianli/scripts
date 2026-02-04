#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title yabai-sp-ds
# @raycast.mode silent
# @raycast.icon 🪟
# @raycast.packageName YABAI

# @tags: yabai, space, destroy

"""
Yabai 删除当前空间
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from common import log_usage

def main():
    log_usage("yabai_sp_ds", "yabai")
    subprocess.run(['yabai', '-m', 'space', '--destroy'])

if __name__ == "__main__":
    main()

