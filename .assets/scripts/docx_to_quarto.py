#!/usr/bin/env python3
"""
docx 一键转换为 Quarto 项目

用法:
    python docx_to_quarto.py <输入.docx>

输出:
    在 docx 同目录生成 quarto_<原文件名>/
    
    quarto_xxx/
    ├── data.yml              # 提取的数据（需人工审核）
    ├── data_mapping.json     # 数据位置映射
    ├── build.py              # 数据处理脚本
    ├── _quarto.yml           # Quarto 配置
    ├── render.sh             # 渲染脚本
    ├── .gitignore
    └── src/
        ├── xxx.qmd           # 模板
        └── variables_template.yml
"""

import argparse
import subprocess
import sys
from pathlib import Path

# 工具目录
TOOLS_DIR = Path(__file__).parent


def run_command(cmd: list, desc: str):
    """运行命令并检查结果"""
    print(f"   {desc}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"   ❌ 失败: {result.stderr}")
        sys.exit(1)
    return result.stdout


def main():
    parser = argparse.ArgumentParser(
        description="docx 一键转换为 Quarto 项目"
    )
    parser.add_argument("input_docx", help="输入的 docx 文件")
    args = parser.parse_args()
    
    input_path = Path(args.input_docx).resolve()
    
    if not input_path.exists():
        print(f"❌ 文件不存在: {input_path}")
        sys.exit(1)
    
    if input_path.suffix.lower() != '.docx':
        print(f"❌ 不是 docx 文件: {input_path}")
        sys.exit(1)
    
    # 文件名（不含扩展名）
    stem = input_path.stem
    
    # 输出目录
    output_dir = input_path.parent / f"quarto_{stem}"
    src_dir = output_dir / "src"
    
    # 临时 md 文件
    temp_md = output_dir / f"{stem}.md"
    
    print("=" * 60)
    print("   docx → Quarto 一键转换")
    print("=" * 60)
    print()
    print(f"📄 输入: {input_path.name}")
    print(f"📁 输出: quarto_{stem}/")
    print()
    
    # Step 1: 创建目录
    print("1️⃣  创建目录...")
    output_dir.mkdir(parents=True, exist_ok=True)
    src_dir.mkdir(exist_ok=True)
    
    # Step 2: docx → md (提取图片)
    print("2️⃣  docx → md (pandoc + 提取图片)...")
    media_dir = output_dir / "media"
    result = subprocess.run(
        ["pandoc", "-f", "docx", "-t", "gfm", 
         f"--extract-media={media_dir}",
         str(input_path), "-o", str(temp_md)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"   ❌ pandoc 失败: {result.stderr}")
        sys.exit(1)
    
    # 统计图片数量
    image_count = 0
    if media_dir.exists():
        image_count = len(list(media_dir.glob("*")))
    print(f"   ✓ {temp_md.name} (图片: {image_count})")
    
    # Step 3: 提取数据
    print("3️⃣  提取数据...")
    result = subprocess.run(
        ["python3", str(TOOLS_DIR / "extract_data.py"), str(temp_md), str(output_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"   ❌ extract_data 失败: {result.stderr}")
        sys.exit(1)
    print("   ✓ data.yml, data_mapping.json")
    
    # Step 4: md → qmd
    print("4️⃣  md → qmd...")
    qmd_path = src_dir / f"{stem}.qmd"
    result = subprocess.run(
        ["python3", str(TOOLS_DIR / "md_to_qmd.py"), 
         str(temp_md), 
         str(output_dir / "data_mapping.json"),
         str(qmd_path)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"   ❌ md_to_qmd 失败: {result.stderr}")
        sys.exit(1)
    print(f"   ✓ src/{stem}.qmd")
    
    # Step 5: 初始化项目
    print("5️⃣  初始化项目结构...")
    result = subprocess.run(
        ["python3", str(TOOLS_DIR / "quarto_init.py"), str(output_dir)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"   ❌ quarto_init 失败: {result.stderr}")
        sys.exit(1)
    print("   ✓ build.py, _quarto.yml, render.sh")
    
    # Step 6: 保留 md 文件
    print("6️⃣  保留原始 md...")
    print(f"   ✓ {temp_md.name}")
    
    print()
    print("=" * 60)
    print("✅ 转换完成!")
    print("=" * 60)
    print()
    print(f"输出目录: {output_dir}")
    print()
    print("下一步:")
    print("  1. 审核并整理 data.yml")
    print("  2. 调整 build.py 添加校验规则")
    print(f"  3. cd \"{output_dir}\" && ./render.sh")
    print()


if __name__ == "__main__":
    main()
