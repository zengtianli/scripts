#!/usr/bin/env python3
"""
前台应用追踪器
每分钟记录当前前台应用到 JSONL 文件
"""

import json
import subprocess
import time
from pathlib import Path


def get_frontmost_app():
    """获取当前前台应用名称"""
    try:
        # 使用 lsappinfo 获取前台应用
        result = subprocess.run(["lsappinfo", "front"], capture_output=True, text=True, check=True)

        # 输出格式: "ASN:0x0-0x12345:"
        asn = result.stdout.strip()
        if not asn:
            return None

        # 获取应用信息
        info_result = subprocess.run(
            ["lsappinfo", "info", "-only", "name", asn], capture_output=True, text=True, check=True
        )

        # 解析输出: "LSDisplayName"="AppName"
        for line in info_result.stdout.split("\n"):
            if '"LSDisplayName"=' in line or '"name"=' in line:
                app_name = line.split("=", 1)[1].strip('"')
                return app_name

        return None

    except subprocess.CalledProcessError as e:
        print(f"Error getting frontmost app: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def log_app_usage(app_name):
    """记录应用使用到 JSONL 文件"""
    log_file = Path.home() / "Library" / "Logs" / "work_tracker.jsonl"

    # 确保日志目录存在
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 记录数据
    record = {"timestamp": int(time.time()), "app": app_name}

    # 追加到文件
    with open(log_file, "a") as f:
        f.write(json.dumps(record) + "\n")


def main():
    app_name = get_frontmost_app()

    if app_name:
        log_app_usage(app_name)
        print(f"Logged: {app_name}")
    else:
        print("Could not determine frontmost app")


if __name__ == "__main__":
    main()
