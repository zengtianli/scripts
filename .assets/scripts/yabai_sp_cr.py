#!/usr/bin/env python3

# @raycast.schemaVersion 1
# @raycast.title yabai-sp-cr
# @raycast.mode silent
# @raycast.icon 🪟
# @raycast.packageName YABAI

# @tags: yabai, space, create

"""
Yabai 创建新空间
"""

import subprocess
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '_lib'))
from common import log_usage

def main():
    log_usage("yabai_sp_cr", "yabai")
    subprocess.run(['yabai', '-m', 'space', '--create'])

if __name__ == "__main__":
    main()

