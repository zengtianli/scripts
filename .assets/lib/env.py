#!/usr/bin/env python3
"""
环境配置模块
动态检测项目路径，不再硬编码
"""

import os
import shutil
from pathlib import Path

# 项目根目录：lib/ 的上两级
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Python 路径：优先使用当前解释器
PYTHON_PATH = shutil.which("python3") or "/usr/bin/env python3"

# 日志文件
USAGE_LOG = os.path.expanduser("~/.useful_scripts_usage.log")
