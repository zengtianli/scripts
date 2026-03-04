#!/usr/bin/env python3


# @tags: yabai, organize, layout

"""
Yabai 整理窗口布局
临时切换到 bsp 模式平铺所有窗口，然后切回 float 模式
"""

import subprocess
import json
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from common import log_usage

def main():
    log_usage("yb_org", "yabai")
    
    # 1. 切换到 bsp 布局（平铺模式）
    subprocess.run(['yabai', '-m', 'space', '--layout', 'bsp'], capture_output=True)
    
    # 2. 平衡所有窗口
    subprocess.run(['yabai', '-m', 'space', '--balance'], capture_output=True)
    
    # 3. 切回 float 布局（不再管理）
    subprocess.run(['yabai', '-m', 'space', '--layout', 'float'], capture_output=True)

if __name__ == "__main__":
    main()

