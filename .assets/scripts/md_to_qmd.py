#!/usr/bin/env python3
"""
将 Markdown 转换为 Quarto 模板
用变量引用替换具体数据值

用法:
    python md_to_qmd.py <报告.md> <data_mapping.json> [输出.qmd]

工作原理:
    1. 读取 data_mapping.json 获取数据位置
    2. 在 Markdown 中将数值替换为 {{< var xxx >}}
    3. 输出 .qmd 模板文件
"""

import argparse
import json
import re
import sys
from pathlib import Path


def load_mapping(mapping_path: Path) -> dict:
    """加载数据映射"""
    with open(mapping_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_var_name(item: dict, index: int) -> str:
    """生成变量名"""
    dtype = item.get('type', 'value')
    return f"data.{dtype}_{index}"


def find_table_ranges(text: str) -> list:
    """找出所有表格的位置范围"""
    ranges = []
    lines = text.split('\n')
    
    char_pos = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        line_start = char_pos
        
        # 检测表格开始
        if line.strip().startswith('|') or '<table' in line.lower():
            table_start = line_start
            while i < len(lines):
                curr_line = lines[i] if i < len(lines) else ''
                if curr_line.strip().startswith('|') or '<table' in curr_line.lower() or \
                   '<tr' in curr_line.lower() or '<td' in curr_line.lower() or \
                   '</table' in curr_line.lower() or curr_line.strip().startswith('|'):
                    char_pos += len(curr_line) + 1
                    i += 1
                    if '</table>' in curr_line.lower():
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


def replace_with_vars(text: str, mapping: dict, skip_tables: bool = True) -> tuple:
    """将文本中的数据替换为变量引用"""
    
    # 找出表格范围
    table_ranges = find_table_ranges(text) if skip_tables else []
    
    # 按位置倒序排序，从后往前替换（避免位置偏移）
    numbers = sorted(mapping.get('numbers', []), 
                    key=lambda x: x['position']['start'], 
                    reverse=True)
    
    replacements = []
    skipped = 0
    
    for i, item in enumerate(numbers):
        start = item['position']['start']
        end = item['position']['end']
        
        # 跳过表格内的数据
        if skip_tables and is_in_table(start, table_ranges):
            skipped += 1
            continue
        
        original = item['full_match']
        var_name = generate_var_name(item, i)
        
        # 替换为 Quarto 变量引用
        var_ref = f"{{{{< var {var_name} >}}}}"
        
        # 执行替换
        text = text[:start] + var_ref + text[end:]
        
        replacements.append({
            'var_name': var_name,
            'original': original,
            'value': item['value'],
            'type': item['type'],
        })
    
    if skipped > 0:
        print(f"   跳过表格内数据 {skipped} 处")
    
    return text, replacements


def add_frontmatter(text: str, title: str = "") -> str:
    """添加 YAML frontmatter"""
    frontmatter = f'''---
title: "{title}"
format: gfm
---

'''
    return frontmatter + text


def generate_variables_template(replacements: list) -> str:
    """生成变量模板（供参考）"""
    lines = [
        "# ============================================",
        "# 变量参考（复制到 data.yml 并填写实际值）",
        "# ============================================",
        "",
        "data:",
    ]
    
    for r in replacements:
        lines.append(f"  {r['var_name'].replace('data.', '')}: {r['value']}  # {r['original']}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="将 Markdown 转换为 Quarto 模板"
    )
    parser.add_argument("input_md", help="输入的 Markdown 文件")
    parser.add_argument("mapping_json", help="数据映射文件 (data_mapping.json)")
    parser.add_argument("output_qmd", nargs="?", help="输出的 QMD 文件（默认同名）")
    parser.add_argument("--title", "-t", default="", help="文档标题")
    args = parser.parse_args()
    
    input_path = Path(args.input_md)
    mapping_path = Path(args.mapping_json)
    
    if args.output_qmd:
        output_path = Path(args.output_qmd)
    else:
        output_path = input_path.with_suffix('.qmd')
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    if not mapping_path.exists():
        print(f"❌ 映射文件不存在: {mapping_path}")
        sys.exit(1)
    
    print(f"📖 读取: {input_path}")
    text = input_path.read_text(encoding='utf-8')
    
    print(f"📦 加载映射: {mapping_path}")
    mapping = load_mapping(mapping_path)
    
    print("🔄 替换数据为变量引用...")
    converted_text, replacements = replace_with_vars(text, mapping)
    print(f"   替换了 {len(replacements)} 处")
    
    # 提取标题
    title = args.title
    if not title:
        # 尝试从第一个 # 标题提取
        match = re.search(r'^#\s+(.+)$', text, re.MULTILINE)
        if match:
            title = match.group(1).strip()
    
    # 添加 frontmatter
    final_text = add_frontmatter(converted_text, title)
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 输出 QMD
    output_path.write_text(final_text, encoding='utf-8')
    print(f"✅ 已生成: {output_path}")
    
    # 输出变量模板
    vars_template_path = output_path.parent / "variables_template.yml"
    vars_template = generate_variables_template(replacements)
    vars_template_path.write_text(vars_template, encoding='utf-8')
    print(f"✅ 变量模板: {vars_template_path}")
    
    print()
    print("下一步:")
    print(f"  1. 审核 {output_path} 中的变量引用")
    print(f"  2. 参考 {vars_template_path} 完善 data.yml")
    print("  3. 运行 ./render.sh 测试渲染")


if __name__ == "__main__":
    main()
