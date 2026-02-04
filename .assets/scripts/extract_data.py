#!/usr/bin/env python3
"""
从 Markdown 报告中提取数据点
生成 data.yml 和 data_mapping.json

用法:
    python extract_data.py <报告.md> [输出目录]

输出:
    data.yml           - 提取的数据
    data_mapping.json  - 数据在原文中的位置映射
"""

import argparse
import json
import re
import sys
from pathlib import Path

import yaml


# ============================================
# 数据提取模式
# ============================================

# 数值模式：数字 + 单位
NUMBER_PATTERNS = [
    # 面积
    (r'(\d+(?:\.\d+)?)\s*(?:平方公里|km²|km2)', 'area_km2'),
    (r'(\d+(?:\.\d+)?)\s*(?:公顷|hm²|hm2)', 'area_hm2'),
    (r'(\d+(?:\.\d+)?)\s*(?:亩)', 'area_mu'),
    
    # 库容
    (r'(\d+(?:\.\d+)?)\s*(?:万m³|万立方米)', 'volume_wanm3'),
    (r'(\d+(?:\.\d+)?)\s*(?:亿m³|亿立方米)', 'volume_yim3'),
    
    # 流量
    (r'(\d+(?:\.\d+)?)\s*(?:m³/s|立方米每秒)', 'flow_m3s'),
    (r'(\d+(?:\.\d+)?)\s*(?:L/s|升每秒)', 'flow_ls'),
    
    # 人口
    (r'(\d+(?:\.\d+)?)\s*(?:万人)', 'population_wan'),
    
    # 金额
    (r'(\d+(?:\.\d+)?)\s*(?:亿元)', 'money_yi'),
    (r'(\d+(?:\.\d+)?)\s*(?:万元)', 'money_wan'),
    
    # 百分比
    (r'(\d+(?:\.\d+)?)\s*(?:%|％)', 'percent'),
    
    # 距离
    (r'(\d+(?:\.\d+)?)\s*(?:km|公里)', 'distance_km'),
    (r'(\d+(?:\.\d+)?)\s*(?:m|米)', 'distance_m'),
    
    # 温度
    (r'(\d+(?:\.\d+)?)\s*(?:℃|°C|摄氏度)', 'temperature'),
    
    # 降水
    (r'(\d+(?:\.\d+)?)\s*(?:mm|毫米)', 'precipitation_mm'),
    
    # 年份
    (r'((?:19|20)\d{2})\s*(?:年)', 'year'),
    
    # 数量
    (r'(\d+)\s*(?:座|个|处|条)', 'count'),
]

# 表格模式
TABLE_PATTERN = r'\|[^\n]+\|'


def find_table_ranges(text: str) -> list:
    """找出所有表格的位置范围"""
    ranges = []
    lines = text.split('\n')
    
    char_pos = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        line_start = char_pos
        
        # 检测表格开始（| 开头或 <table）
        if line.strip().startswith('|') or '<table' in line.lower():
            table_start = line_start
            # 找表格结束
            while i < len(lines):
                if lines[i].strip().startswith('|') or '<table' in lines[i].lower() or \
                   '<tr' in lines[i].lower() or '<td' in lines[i].lower() or \
                   '</table' in lines[i].lower() or lines[i].strip().startswith('|'):
                    char_pos += len(lines[i]) + 1
                    i += 1
                    # 如果是 </table> 或空行，表格结束
                    if '</table>' in lines[i-1].lower() or (i < len(lines) and not lines[i].strip().startswith('|') and '<' not in lines[i]):
                        break
                else:
                    break
            table_end = char_pos
            ranges.append((table_start, table_end))
        else:
            char_pos += len(line) + 1
            i += 1
    
    return ranges


def is_in_table(pos: int, table_ranges: list) -> bool:
    """检查位置是否在表格内"""
    for start, end in table_ranges:
        if start <= pos < end:
            return True
    return False


def extract_numbers(text: str, skip_tables: bool = True) -> list:
    """提取所有数值数据"""
    results = []
    
    # 找出表格范围
    table_ranges = find_table_ranges(text) if skip_tables else []
    
    for pattern, dtype in NUMBER_PATTERNS:
        for match in re.finditer(pattern, text):
            start = match.start()
            end = match.end()
            
            # 跳过表格内的数据
            if skip_tables and is_in_table(start, table_ranges):
                continue
            
            value = match.group(1)
            
            # 获取上下文（前后各50字符）
            ctx_start = max(0, start - 50)
            ctx_end = min(len(text), end + 50)
            context = text[ctx_start:ctx_end].replace('\n', ' ').strip()
            
            results.append({
                'value': float(value) if '.' in value else int(value),
                'type': dtype,
                'full_match': match.group(0),
                'position': {'start': start, 'end': end},
                'context': context,
            })
    
    return results


def extract_tables(text: str) -> list:
    """提取表格"""
    tables = []
    lines = text.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(TABLE_PATTERN, line):
            # 找到表格开始
            table_lines = []
            start_line = i
            while i < len(lines) and (re.match(TABLE_PATTERN, lines[i]) or lines[i].strip().startswith('|')):
                table_lines.append(lines[i])
                i += 1
            
            if len(table_lines) >= 2:  # 至少有表头和分隔符
                tables.append({
                    'lines': table_lines,
                    'start_line': start_line + 1,  # 1-indexed
                    'end_line': i,
                })
        else:
            i += 1
    
    return tables


def parse_table(table_lines: list) -> dict:
    """解析表格为结构化数据"""
    if len(table_lines) < 2:
        return None
    
    # 解析表头
    header_line = table_lines[0]
    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    
    # 跳过分隔符行
    data_start = 1
    if len(table_lines) > 1 and re.match(r'^\|[\s\-:]+\|', table_lines[1]):
        data_start = 2
    
    # 解析数据行
    rows = []
    for line in table_lines[data_start:]:
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) == len(headers):
            row = dict(zip(headers, cells))
            rows.append(row)
    
    return {
        'headers': headers,
        'rows': rows,
    }


def group_by_context(numbers: list) -> dict:
    """按上下文关键词分组数据"""
    groups = {
        '基本信息': [],
        '区域概况': [],
        '水库': [],
        '流量': [],
        '其他': [],
    }
    
    for item in numbers:
        ctx = item['context'].lower()
        
        if any(k in ctx for k in ['集雨', '库容', '水库', '坝址']):
            groups['水库'].append(item)
        elif any(k in ctx for k in ['生态流量', '下泄', 'm³/s']):
            groups['流量'].append(item)
        elif any(k in ctx for k in ['面积', '人口', 'gdp', '降水', '气温']):
            groups['区域概况'].append(item)
        elif any(k in ctx for k in ['县', '市', '年', '报告']):
            groups['基本信息'].append(item)
        else:
            groups['其他'].append(item)
    
    return groups


def build_data_yml(groups: dict, tables: list) -> str:
    """构建 data.yml 内容"""
    lines = [
        "# ============================================",
        "# 自动提取的数据（需人工审核）",
        "# ============================================",
        "",
    ]
    
    for group_name, items in groups.items():
        if not items:
            continue
        
        lines.append(f"# ====== {group_name} ======")
        lines.append(f"{group_name}:")
        
        seen = set()
        for item in items:
            key = f"{item['type']}_{item['value']}"
            if key in seen:
                continue
            seen.add(key)
            
            # 从上下文提取可能的字段名
            ctx = item['context']
            lines.append(f"  # {ctx[:60]}...")
            lines.append(f"  {item['type']}: {item['value']}  # {item['full_match']}")
        
        lines.append("")
    
    # 添加表格数据
    if tables:
        lines.append("# ====== 表格数据 ======")
        for i, table in enumerate(tables):
            parsed = parse_table(table['lines'])
            if parsed and parsed['rows']:
                lines.append(f"# 表格 {i+1} (行 {table['start_line']}-{table['end_line']})")
                lines.append(f"表格{i+1}:")
                for j, row in enumerate(parsed['rows'][:5]):  # 只取前5行
                    lines.append(f"  行{j+1}:")
                    for k, v in row.items():
                        # 清理值
                        v_clean = re.sub(r'<[^>]+>', '', str(v)).strip()
                        if v_clean:
                            lines.append(f"    {k}: \"{v_clean}\"")
                lines.append("")
    
    return '\n'.join(lines)


def build_mapping(numbers: list, tables: list) -> dict:
    """构建数据位置映射"""
    return {
        'numbers': [
            {
                'value': item['value'],
                'type': item['type'],
                'full_match': item['full_match'],
                'position': item['position'],
            }
            for item in numbers
        ],
        'tables': [
            {
                'start_line': t['start_line'],
                'end_line': t['end_line'],
            }
            for t in tables
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="从 Markdown 报告中提取数据点"
    )
    parser.add_argument("input_md", help="输入的 Markdown 文件")
    parser.add_argument("output_dir", nargs="?", default=".", help="输出目录")
    args = parser.parse_args()
    
    input_path = Path(args.input_md)
    output_dir = Path(args.output_dir)
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    print(f"📖 读取: {input_path}")
    text = input_path.read_text(encoding='utf-8')
    
    print("🔍 提取数值数据...")
    numbers = extract_numbers(text)
    print(f"   找到 {len(numbers)} 个数值")
    
    print("📊 提取表格...")
    tables = extract_tables(text)
    print(f"   找到 {len(tables)} 个表格")
    
    print("📦 按上下文分组...")
    groups = group_by_context(numbers)
    
    # 输出 data.yml
    output_dir.mkdir(parents=True, exist_ok=True)
    data_yml_path = output_dir / "data.yml"
    data_yml_content = build_data_yml(groups, tables)
    data_yml_path.write_text(data_yml_content, encoding='utf-8')
    print(f"✅ 已生成: {data_yml_path}")
    
    # 输出 mapping
    mapping_path = output_dir / "data_mapping.json"
    mapping = build_mapping(numbers, tables)
    mapping_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f"✅ 已生成: {mapping_path}")
    
    print()
    print("⚠️  注意: 自动提取的数据需要人工审核和整理!")


if __name__ == "__main__":
    main()
