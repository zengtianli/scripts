#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title xlsx-field-map
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
# @raycast.description Map Excel fields
"""
Excel 字段映射工具

功能：
1. 从一个Excel表格读取数据，按字段映射生成新表格
2. 支持字段重命名、值转换、单位转换
3. 支持多列合并

使用示例：
    # 使用映射配置文件
    python field_mapper.py input.xlsx -m mapping.json -o output.xlsx
    
    # 命令行指定映射
    python field_mapper.py input.xlsx --map "新列名=旧列名" --map "列B=列A" -o output.xlsx
    
    # 添加常量列
    python field_mapper.py input.xlsx --const "状态=待处理" -o output.xlsx
"""

import json
import argparse
from pathlib import Path

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    print("❌ 此工具需要安装pandas: pip install pandas openpyxl")


# ==================== 值转换函数 ====================

def convert_wan_to_yi(value):
    """万 → 亿（÷10000）"""
    if pd.isna(value) or value == '':
        return ''
    try:
        return round(float(value) / 10000, 4)
    except:
        return ''


def convert_yi_to_wan(value):
    """亿 → 万（×10000）"""
    if pd.isna(value) or value == '':
        return ''
    try:
        return round(float(value) * 10000, 2)
    except:
        return ''


def convert_bool_cn(value, true_values=None, false_values=None):
    """转换为中文是/否"""
    if pd.isna(value):
        return '否'
    
    value = str(value).strip()
    
    if true_values is None:
        true_values = ['是', 'yes', 'true', '1', 'Y', 'y']
    if false_values is None:
        false_values = ['否', 'no', 'false', '0', 'N', 'n', '-', '/', '']
    
    if value in true_values or (value not in false_values and value):
        return '是'
    return '否'


def truncate_text(value, max_length=30):
    """截断文本"""
    if pd.isna(value) or value == '':
        return ''
    text = str(value)
    return text[:max_length] if len(text) > max_length else text


# 内置转换器
CONVERTERS = {
    'wan_to_yi': convert_wan_to_yi,
    'yi_to_wan': convert_yi_to_wan,
    'bool_cn': convert_bool_cn,
    'truncate': truncate_text,
}


# ==================== 字段映射 ====================

def apply_mapping(df, mapping_config):
    """
    应用字段映射
    
    Args:
        df: 输入DataFrame
        mapping_config: 映射配置
            {
                "fields": [
                    {"target": "新列名", "source": "旧列名"},
                    {"target": "列B", "source": "列A", "converter": "wan_to_yi"},
                    {"target": "状态", "value": "待处理"},  # 常量
                    {"target": "合并列", "sources": ["列1", "列2"], "separator": "、"},
                ],
                "drop_empty_rows": true,
                "output_columns": ["列1", "列2", "列3"]  # 可选，指定输出列顺序
            }
    
    Returns:
        DataFrame: 映射后的数据
    """
    result = pd.DataFrame()
    
    fields = mapping_config.get('fields', [])
    
    for field in fields:
        target = field.get('target')
        if not target:
            continue
        
        # 常量值
        if 'value' in field:
            result[target] = field['value']
            continue
        
        # 多列合并
        if 'sources' in field:
            sources = field['sources']
            separator = field.get('separator', '、')
            
            def merge_columns(row):
                values = []
                for src in sources:
                    if src in df.columns:
                        val = row.get(src, '')
                        if pd.notna(val) and str(val).strip():
                            values.append(str(val).strip())
                return separator.join(values)
            
            result[target] = df.apply(merge_columns, axis=1)
            continue
        
        # 单列映射
        source = field.get('source', target)
        
        if source not in df.columns:
            # 尝试查找相似列名
            similar = [c for c in df.columns if source in c or c in source]
            if similar:
                source = similar[0]
            else:
                result[target] = ''
                continue
        
        # 复制数据
        result[target] = df[source].copy()
        
        # 应用转换器
        converter_name = field.get('converter')
        if converter_name and converter_name in CONVERTERS:
            result[target] = result[target].apply(CONVERTERS[converter_name])
        
        # 自定义转换（lambda表达式）
        if 'transform' in field:
            try:
                transform_func = eval(f"lambda x: {field['transform']}")
                result[target] = result[target].apply(transform_func)
            except Exception as e:
                print(f"⚠️  转换表达式错误 ({target}): {e}")
    
    # 删除空行
    if mapping_config.get('drop_empty_rows', False):
        result = result.dropna(how='all')
    
    # 指定列顺序
    if 'output_columns' in mapping_config:
        columns = mapping_config['output_columns']
        # 确保所有列都存在
        for col in columns:
            if col not in result.columns:
                result[col] = ''
        result = result[columns]
    
    return result


def parse_cli_mapping(map_strings, const_strings=None):
    """
    解析命令行映射参数
    
    Args:
        map_strings: ["新列=旧列", "列B=列A:wan_to_yi"]
        const_strings: ["状态=待处理"]
    
    Returns:
        dict: 映射配置
    """
    fields = []
    
    # 解析字段映射
    if map_strings:
        for m in map_strings:
            if '=' not in m:
                continue
            
            target, source_part = m.split('=', 1)
            target = target.strip()
            
            # 检查是否有转换器
            if ':' in source_part:
                source, converter = source_part.rsplit(':', 1)
                fields.append({
                    'target': target,
                    'source': source.strip(),
                    'converter': converter.strip()
                })
            else:
                fields.append({
                    'target': target,
                    'source': source_part.strip()
                })
    
    # 解析常量
    if const_strings:
        for c in const_strings:
            if '=' not in c:
                continue
            target, value = c.split('=', 1)
            fields.append({
                'target': target.strip(),
                'value': value.strip()
            })
    
    return {'fields': fields}


# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(
        description='Excel字段映射工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例：

1. 使用映射配置文件：
   python field_mapper.py input.xlsx -m mapping.json -o output.xlsx

2. 命令行指定映射：
   python field_mapper.py input.xlsx --map "新列=旧列" --map "库容=总库容:wan_to_yi" -o output.xlsx

3. 添加常量列：
   python field_mapper.py input.xlsx --map "名称=水库名称" --const "状态=待处理" -o output.xlsx

4. 生成映射模板：
   python field_mapper.py input.xlsx --generate-template -o mapping_template.json

映射配置文件格式 (JSON)：
{
  "fields": [
    {"target": "新列名", "source": "旧列名"},
    {"target": "库容(亿m³)", "source": "总库容(万m³)", "converter": "wan_to_yi"},
    {"target": "状态", "value": "待处理"},
    {"target": "位置", "sources": ["省", "市", "县"], "separator": ""}
  ],
  "output_columns": ["序号", "名称", "库容(亿m³)", "状态"]
}

可用转换器：
  - wan_to_yi: 万 → 亿（÷10000）
  - yi_to_wan: 亿 → 万（×10000）
  - bool_cn: 转换为中文是/否
  - truncate: 截断文本（默认30字符）
        """
    )
    
    parser.add_argument('input', help='输入Excel文件')
    parser.add_argument('-m', '--mapping', help='映射配置文件（JSON）')
    parser.add_argument('--map', action='append', help='字段映射（新列=旧列 或 新列=旧列:转换器）')
    parser.add_argument('--const', action='append', help='常量列（列名=值）')
    parser.add_argument('-o', '--output', required=True, help='输出文件')
    parser.add_argument('-s', '--sheet', default=0, help='输入sheet名称或索引（默认0）')
    parser.add_argument('--generate-template', action='store_true', help='生成映射模板')
    parser.add_argument('--list-converters', action='store_true', help='列出可用转换器')
    
    args = parser.parse_args()
    
    if not HAS_PANDAS:
        return
    
    # 列出转换器
    if args.list_converters:
        print("📚 可用转换器：")
        for name, func in CONVERTERS.items():
            print(f"  - {name}: {func.__doc__.strip()}")
        return
    
    # 读取输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        return
    
    try:
        sheet = int(args.sheet)
    except:
        sheet = args.sheet
    
    df = pd.read_excel(input_path, sheet_name=sheet)
    print(f"📂 读取: {input_path.name}")
    print(f"   {len(df)} 行, {len(df.columns)} 列")
    
    # 生成模板
    if args.generate_template:
        template = {
            "fields": [
                {"target": col, "source": col}
                for col in df.columns
            ],
            "output_columns": list(df.columns)
        }
        
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template, f, ensure_ascii=False, indent=2)
        
        print(f"💾 模板已保存: {output_path}")
        return
    
    # 获取映射配置
    if args.mapping:
        mapping_path = Path(args.mapping)
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping_config = json.load(f)
    else:
        mapping_config = parse_cli_mapping(args.map, args.const)
    
    if not mapping_config.get('fields'):
        print("❌ 未指定映射规则")
        print("   使用 --map 或 -m 指定映射")
        return
    
    # 应用映射
    print(f"\n🔄 应用映射...")
    result = apply_mapping(df, mapping_config)
    
    # 保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_excel(output_path, index=False)
    
    print(f"\n💾 已保存: {output_path}")
    print(f"   {len(result)} 行, {len(result.columns)} 列")
    print(f"   列: {list(result.columns)}")


if __name__ == "__main__":
    main()

