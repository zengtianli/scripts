#!/usr/bin/env python3
"""
CSV 核心功能模块
提供所有 CSV 相关的转换和处理功能
"""

import csv
import re
from pathlib import Path
from typing import Optional, List

# 尝试导入可选依赖
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


def detect_delimiter(content: str) -> str:
    """检测文本分隔符"""
    delimiters = ['\t', ',', ';', '|']
    counts = {d: content.count(d) for d in delimiters}
    return max(counts, key=counts.get)


def txt_to_csv(input_file: Path, output_file: Optional[Path] = None) -> bool:
    """
    TXT 转 CSV
    自动检测分隔符
    """
    if output_file is None:
        output_file = input_file.with_suffix('.csv')
    
    try:
        content = input_file.read_text(encoding='utf-8')
        delimiter = detect_delimiter(content)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for line in content.splitlines():
                if line.strip():
                    writer.writerow(line.split(delimiter))
        return True
    except Exception:
        return False


def csv_to_txt(input_file: Path, output_file: Optional[Path] = None, delimiter: str = '\t') -> bool:
    """
    CSV 转 TXT
    默认使用 Tab 分隔
    """
    if output_file is None:
        output_file = input_file.with_suffix('.txt')
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in, \
             open(output_file, 'w', encoding='utf-8') as f_out:
            reader = csv.reader(f_in)
            for row in reader:
                f_out.write(delimiter.join(row) + '\n')
        return True
    except Exception:
        return False


def csv_to_xlsx(input_file: Path, output_file: Optional[Path] = None) -> bool:
    """
    CSV/TXT 转 XLSX
    需要 pandas 和 openpyxl
    """
    if not HAS_PANDAS:
        raise ImportError("需要安装 pandas: pip install pandas openpyxl")
    
    if output_file is None:
        output_file = input_file.with_suffix('.xlsx')
    
    try:
        # 检测是 CSV 还是 TXT
        if input_file.suffix.lower() == '.txt':
            df = pd.read_csv(input_file, sep='\t', encoding='utf-8', engine='python')
        else:
            df = pd.read_csv(input_file, encoding='utf-8')
        
        df.to_excel(output_file, index=False)
        return True
    except Exception:
        return False


def merge_txt_files(directory: Path, output_file: Optional[Path] = None) -> bool:
    """
    合并目录中所有 TXT 文件为 CSV
    按文件名中的数字排序
    """
    if output_file is None:
        output_file = directory / 'merged.csv'
    
    txt_files = sorted(directory.glob('*.txt'))
    if not txt_files:
        return False
    
    def extract_number(f: Path):
        match = re.match(r'(\d+)', f.name)
        return int(match.group(1)) if match else float('inf')
    
    txt_files.sort(key=extract_number)
    
    # 找最长文件的行数
    max_lines = 0
    for file in txt_files:
        with open(file, 'r', encoding='utf-8') as f:
            max_lines = max(max_lines, sum(1 for _ in f))
    
    if max_lines == 0:
        output_file.touch()
        return True
    
    lines = [[] for _ in range(max_lines)]
    
    for file in txt_files:
        with open(file, 'r', encoding='utf-8') as f:
            file_lines = [line.strip() for line in f.readlines()]
            for i in range(max_lines):
                lines[i].append(file_lines[i] if i < len(file_lines) else '')
    
    try:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(lines)
        return True
    except Exception:
        return False


def reorder_csv(input_file: Path, order_file: Path, output_file: Optional[Path] = None) -> bool:
    """
    根据列表文件重排 CSV 行
    """
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_ordered.csv"
    
    try:
        # 读取排序列表
        with open(order_file, 'r', encoding='utf-8') as f:
            order_list = [row[0].strip() for row in csv.reader(f)]
        
        # 读取 CSV
        with open(input_file, 'r', encoding='utf-8-sig') as f:
            csv_data = list(csv.reader(f))
        
        # 创建字典
        data_dict = {row[0].lstrip('\ufeff').strip(): row for row in csv_data}
        
        ordered_data = []
        found_keys = set()
        
        for name in order_list:
            clean_name = name.strip()
            if clean_name in data_dict:
                ordered_data.append(data_dict[clean_name])
                found_keys.add(clean_name)
            elif clean_name.replace('（在建）', '') in data_dict:
                key = clean_name.replace('（在建）', '')
                ordered_data.append(data_dict[key])
                found_keys.add(key)
        
        # 追加未匹配的行
        for key, row in data_dict.items():
            if key not in found_keys:
                ordered_data.append(row)
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(ordered_data)
        
        return True
    except Exception:
        return False


def format_circles(input_file: Path, output_file: Optional[Path] = None) -> bool:
    """
    格式化带圈数字
    将 ① ② ③ 等转换为 1. 2. 3. 等
    """
    if output_file is None:
        output_file = input_file.parent / f"{input_file.stem}_formatted.csv"
    
    # 带圈数字映射
    circle_map = {
        '①': '1.', '②': '2.', '③': '3.', '④': '4.', '⑤': '5.',
        '⑥': '6.', '⑦': '7.', '⑧': '8.', '⑨': '9.', '⑩': '10.',
        '⑪': '11.', '⑫': '12.', '⑬': '13.', '⑭': '14.', '⑮': '15.',
    }
    
    try:
        content = input_file.read_text(encoding='utf-8')
        
        for circle, number in circle_map.items():
            content = content.replace(circle, number)
        
        output_file.write_text(content, encoding='utf-8')
        return True
    except Exception:
        return False

