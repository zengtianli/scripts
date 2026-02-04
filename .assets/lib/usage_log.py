#!/Users/tianli/miniforge3/bin/python3
"""
使用统计日志模块
"""

import os
import csv
from datetime import datetime

from constants import USAGE_LOG


def log_usage(script_name: str, category: str = ""):
    """
    记录脚本使用统计
    
    Args:
        script_name: 脚本名称
        category: 分类
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 如果日志文件不存在，创建并写入表头
        if not os.path.exists(USAGE_LOG):
            with open(USAGE_LOG, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'script_name', 'category'])
        
        # 追加记录
        with open(USAGE_LOG, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, script_name, category])
    except Exception:
        pass  # 静默失败，不影响主流程

