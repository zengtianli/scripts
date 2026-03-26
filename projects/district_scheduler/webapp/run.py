#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
河区调度模型 - 命令行入口

用法：
    python run.py                    # 使用示例数据
    python run.py /path/to/data      # 指定数据目录
"""
import sys
from pathlib import Path

# 添加 src 到路径
SRC_DIR = Path(__file__).parent / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from scheduler import DistrictScheduler


def main():
    # 确定数据路径
    if len(sys.argv) > 1:
        data_path = Path(sys.argv[1])
    else:
        data_path = Path(__file__).parent / 'data' / 'sample'
    
    if not data_path.exists():
        print(f"错误: 数据目录不存在: {data_path}")
        sys.exit(1)
    
    print(f"使用数据目录: {data_path}")
    print("=" * 50)
    
    # 创建调度器并运行
    scheduler = DistrictScheduler(data_path=data_path)
    results = scheduler.run()
    
    print("=" * 50)
    if results.get('status') == 'success':
        print("✅ 计算完成！")
        print(f"处理河区数: {results.get('districts_processed', 0)}")
        print(f"总需水量: {results.get('total_water_demand', 0):.2f} 万m³")
        print(f"总供水量: {results.get('total_water_supply', 0):.2f} 万m³")
        print(f"缺水量: {results.get('total_shortage', 0):.2f} 万m³")
    else:
        print(f"❌ 计算失败: {results.get('message')}")
        sys.exit(1)


if __name__ == '__main__':
    main()

