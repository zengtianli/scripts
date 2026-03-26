#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本

使用方式：
    python run.py          # 启动 Web 界面
    python run.py --reload # 强制刷新数据缓存
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent


def main():
    # 检查是否需要刷新缓存
    if "--reload" in sys.argv:
        print("🔄 刷新数据缓存...")
        cache_file = PROJECT_ROOT / "data" / "cache" / "all_years.csv"
        if cache_file.exists():
            cache_file.unlink()
            print("✅ 缓存已清除")
    
    # 启动 Streamlit
    app_path = PROJECT_ROOT / "app.py"
    print("🚀 启动 Web 界面...")
    print(f"📍 访问地址: http://localhost:8501")
    
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(app_path),
        "--server.port", "8501",
    ])


if __name__ == "__main__":
    main()


