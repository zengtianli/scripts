#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
灌溉需水模型 - 命令行入口

使用方式：
    python run.py                           # 使用 data/input/ 目录
    python run.py /path/to/data             # 指定数据目录
    python run.py --help                    # 查看帮助
"""
import sys
import os
from pathlib import Path

# 添加 src 目录到 path
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR / 'src'))

# 默认数据目录
DEFAULT_DATA_DIR = PROJECT_DIR / 'data' / 'input'


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='浙东灌溉需水计算模型',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
    python run.py                    # 使用默认数据目录
    python run.py /path/to/data      # 指定数据目录
    python run.py --b3               # B3 NC数据模式
        """
    )
    
    parser.add_argument('data_dir', nargs='?', default=str(DEFAULT_DATA_DIR),
                        help='数据目录路径（默认: data/input/）')
    parser.add_argument('--b3', dest='b3_mode', action='store_true',
                        help='启用 B3 NC 数据格式模式')
    parser.add_argument('--year', type=int, default=None,
                        help='B3 数据年份')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='安静模式')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='详细模式')
    
    args = parser.parse_args()
    
    # 检查数据目录
    data_path = Path(args.data_dir)
    if not data_path.exists():
        print(f"错误: 数据目录不存在: {data_path}")
        sys.exit(1)
    
    # 设置输出目录
    output_dir = PROJECT_DIR / 'data' / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    os.environ['IRRIGATION_OUTPUT_DIR'] = str(output_dir)
    
    # 切换到数据目录运行
    original_dir = os.getcwd()
    os.chdir(data_path)
    
    try:
        # 导入并运行主程序
        from main import main as run_main
        
        # 构造原始参数
        sys.argv = ['main.py']
        if args.b3_mode:
            sys.argv.append('--b3')
        if args.year:
            sys.argv.extend(['--year', str(args.year)])
        if args.quiet:
            sys.argv.append('-q')
        if args.verbose:
            sys.argv.append('-v')
        
        run_main()
        
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    main()

