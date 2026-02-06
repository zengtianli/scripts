#!/Users/tianli/miniforge3/bin/python3
# @raycast.schemaVersion 1
# @raycast.title md-format
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Scripts
# @raycast.description Format markdown
# -*- coding: utf-8 -*-
"""
文本格式自动修复工具
支持批量处理Markdown文件中的格式问题

功能列表：

1. 双引号格式修复
   将所有双引号统一为中文标准引号："和"
   奇数个引号 → " (中文左双引号 U+201C)
   偶数个引号 → " (中文右双引号 U+201D)

2. 英文标点符号转中文
   , → ，  (逗号)
   : → ：  (冒号)
   ; → ；  (分号)
   ! → ！  (感叹号)
   ? → ？  (问号)
   ( → （  (左括号)
   ) → ）  (右括号)

3. 中文单位转标准符号
   面积：平方米 → m²、平方公里 → km²
   体积：立方米 → m³、立方厘米 → cm³
   长度：公里 → km、厘米 → cm、毫米 → mm
   质量：公斤 → kg、毫克 → mg
   容量：毫升 → mL、微升 → μL
   时间：小时 → h、分钟 → min、秒钟 → s
   温度：摄氏度 → ℃、华氏度 → ℉

使用方法：
    python3 text_formatter.py 文件名.md
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "lib"))
from common_utils import get_input_files


def fix_quotes(content):
    """
    替换所有双引号为中文标准引号
    奇数位置 → " (左引号)
    偶数位置 → " (右引号)
    """
    # 匹配所有可能的双引号类型
    # ", ", ", ", 「, 」以及英文双引号"
    quote_pattern = r'["""''「」]'
    
    # 计数器，用于判断奇偶
    counter = 0
    
    def replace_quote(match):
        nonlocal counter
        counter += 1
        # 奇数用中文左引号"，偶数用中文右引号"
        return '“' if counter % 2 == 1 else '”'
    # 执行替换
    result = re.sub(quote_pattern, replace_quote, content)
    
    return result, counter


def fix_punctuation(content):
    """
    将英文标点符号转换为中文标点符号
    """
    # 英文标点到中文标点的映射
    punctuation_map = {
        ',': '，',   # 逗号
        ':': '：',   # 冒号
        ';': '；',   # 分号
        '!': '！',   # 感叹号
        '?': '？',   # 问号
        '(': '（',   # 左括号
        ')': '）',   # 右括号
    }
    
    result = content
    replacement_count = 0
    
    # 逐个替换标点符号
    for eng_punct, chn_punct in punctuation_map.items():
        # 转义特殊字符
        escaped_punct = re.escape(eng_punct)
        count = len(re.findall(escaped_punct, result))
        replacement_count += count
        result = re.sub(escaped_punct, chn_punct, result)
    
    return result, replacement_count


def fix_units(content):
    """
    将中文单位转换为标准符号单位
    """
    # 中文单位到符号的映射（按长度排序，优先匹配长的）
    units_map = {
        # 面积单位
        '平方公里': 'km²',
        '平方千米': 'km²',
        '平方米': 'm²',
        '平方厘米': 'cm²',
        '平方毫米': 'mm²',
        
        # 体积单位
        '立方米': 'm³',
        '立方厘米': 'cm³',
        '立方毫米': 'mm³',
        '立方公里': 'km³',
        '立方千米': 'km³',
        
        # 长度单位
        '公里': 'km',
        '千米': 'km',
        '厘米': 'cm',
        '毫米': 'mm',
        '微米': 'μm',
        '纳米': 'nm',
        
        # 质量单位
        '公斤': 'kg',
        '千克': 'kg',
        '毫克': 'mg',
        '微克': 'μg',
        
        # 容量单位
        '毫升': 'mL',
        '微升': 'μL',
        
        # 时间单位
        '小时': 'h',
        '分钟': 'min',
        '秒钟': 's',
        
        # 温度单位
        '摄氏度': '℃',
        '华氏度': '℉',
    }
    
    result = content
    replacement_count = 0
    
    # 按长度从长到短排序，避免误匹配（如"平方米"要在"米"之前）
    sorted_units = sorted(units_map.items(), key=lambda x: len(x[0]), reverse=True)
    
    for chn_unit, symbol in sorted_units:
        count = result.count(chn_unit)
        if count > 0:
            replacement_count += count
            result = result.replace(chn_unit, symbol)
    
    return result, replacement_count


def process_file(input_file):
    """
    处理单个文件
    """
    input_path = Path(input_file)
    
    if not input_path.exists():
        print(f"❌ 错误：文件不存在 - {input_file}")
        return False
    
    # 生成输出文件名
    output_path = input_path.parent / f"{input_path.stem}_fixed{input_path.suffix}"
    
    try:
        # 读取文件
        print(f"📖 正在读取文件: {input_path.name}")
        with open(input_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 处理引号
        print(f"🔄 正在处理引号...")
        fixed_content, quote_count = fix_quotes(content)
        
        # 处理标点符号
        print(f"🔄 正在处理标点符号...")
        fixed_content, punct_count = fix_punctuation(fixed_content)
        
        # 处理单位转换
        print(f"🔄 正在转换单位...")
        fixed_content, unit_count = fix_units(fixed_content)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"✅ 处理完成！")
        print(f"   - 共替换了 {quote_count} 个引号")
        print(f"   - 共替换了 {punct_count} 个标点符号")
        print(f"   - 共转换了 {unit_count} 个单位")
        print(f"   - 输出文件: {output_path.name}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理失败：{e}")
        return False


if __name__ == "__main__":
    # 获取输入文件（优先命令行参数，否则从 Finder 获取）
    files = get_input_files(sys.argv[1:], expected_ext='md', allow_multiple=False)
    
    if not files:
        print("❌ 错误：缺少文件名参数")
        print("\n使用方法：")
        print("    python3 text_formatter.py 文件名.md")
        print("    或在 Finder 中选择 .md 文件后运行")
        print("\n示例：")
        print("    python3 text_formatter.py ztl-1.md")
        sys.exit(1)
    
    input_file = files[0]
    
    print("=" * 50)
    print("文本格式自动修复工具")
    print("=" * 50)
    
    success = process_file(input_file)
    
    if success:
        print("\n🎉 全部完成！")
    else:
        print("\n❌ 处理失败，请检查错误信息")
        sys.exit(1)

