#!/usr/bin/env python3
"""
Quarto 项目初始化工具
在指定目录创建 Quarto 数据驱动报告的标准结构

用法:
    python quarto_init.py <项目目录>
    python quarto_init.py .

生成结构:
    <项目目录>/
    ├── data.yml          # 原始数据（需手动填写）
    ├── build.py          # 数据处理脚本
    ├── _quarto.yml       # Quarto 配置
    ├── render.sh         # 渲染脚本
    ├── src/              # qmd 模板目录
    └── .gitignore        # Git 忽略规则
"""

import argparse
import os
from pathlib import Path

# ============================================
# 模板内容
# ============================================

DATA_YML_TEMPLATE = """# ============================================
# 项目数据文件
# 只存原始数据，派生数据由 build.py 计算
# ============================================

# ====== 基本信息 ======
基本信息:
  项目名: ""
  报告日期: ""

# ====== 数据区 ======
# 在此添加项目特定数据
"""

BUILD_PY_TEMPLATE = '''#!/usr/bin/env python3
"""
数据处理脚本
读取 data.yml，校验数据，生成 _variables.yml
"""

import yaml
import sys


def load_data():
    with open("data.yml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_data(data):
    """数据合理性校验"""
    errors = []
    
    # ====== 基本校验 ======
    基本信息 = data.get("基本信息", {})
    if not 基本信息.get("项目名"):
        errors.append("缺少项目名")
    
    # TODO: 添加项目特定校验规则
    
    return errors


def build_variables(data):
    """计算派生数据，构建变量字典"""
    variables = {}
    
    # 直接复制基本信息
    variables["基本信息"] = data.get("基本信息", {})
    
    # TODO: 添加派生数据计算
    
    return variables


def save_variables(variables):
    header = """# ============================================
# 自动生成，请勿手动修改！
# 修改 data.yml 后运行 python build.py
# ============================================

"""
    with open("_variables.yml", "w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(variables, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


def main():
    print("📖 读取 data.yml...")
    data = load_data()

    print("🔍 校验数据合理性...")
    errors = validate_data(data)
    if errors:
        print("\\n❌ 数据校验失败:")
        for e in errors:
            print(f"  - {e}")
        print("\\n请修正 data.yml 后重试。")
        sys.exit(1)
    print("✓ 数据校验通过")

    print("🔢 计算派生数据...")
    variables = build_variables(data)

    print("💾 生成 _variables.yml...")
    save_variables(variables)

    print("\\n✅ 完成!")


if __name__ == "__main__":
    main()
'''

QUARTO_YML_TEMPLATE = """project:
  type: default
  output-dir: .

format:
  gfm:
    wrap: none

metadata-files:
  - _variables.yml
"""

RENDER_SH_TEMPLATE = """#!/bin/bash
# Quarto 渲染脚本
# 用法: ./render.sh

set -e

echo "=========================================="
echo "   Quarto 数据驱动报告渲染"
echo "=========================================="
echo ""

echo "1️⃣  生成 _variables.yml..."
python3 build.py

echo ""
echo "2️⃣  Quarto 渲染..."
for qmd in src/*.qmd; do
    if [ -f "$qmd" ]; then
        filename=$(basename "$qmd" .qmd)
        quarto render "$qmd" --to gfm
        mv "src/${filename}.md" "./${filename}.md"
        echo "   ✓ ${filename}.md"
    fi
done

echo ""
echo "=========================================="
echo "✅ 渲染完成！"
echo "=========================================="
"""

GITIGNORE_TEMPLATE = """# Quarto 生成的文件
_variables.yml
*.md
!README.md
.quarto/

# 产物
*.docx
*.pdf
"""


def init_project(project_dir: Path):
    """初始化 Quarto 项目"""

    # 创建目录
    project_dir.mkdir(parents=True, exist_ok=True)
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)

    # 写入文件（不覆盖已存在的）
    files = {
        "data.yml": DATA_YML_TEMPLATE,
        "build.py": BUILD_PY_TEMPLATE,
        "_quarto.yml": QUARTO_YML_TEMPLATE,
        "render.sh": RENDER_SH_TEMPLATE,
        ".gitignore": GITIGNORE_TEMPLATE,
    }

    created = []
    skipped = []

    for filename, content in files.items():
        filepath = project_dir / filename
        if filepath.exists():
            skipped.append(filename)
        else:
            filepath.write_text(content, encoding="utf-8")
            created.append(filename)

    # 设置 render.sh 可执行
    render_sh = project_dir / "render.sh"
    if render_sh.exists():
        os.chmod(render_sh, 0o755)

    return created, skipped


def main():
    parser = argparse.ArgumentParser(description="初始化 Quarto 数据驱动报告项目")
    parser.add_argument("project_dir", nargs="?", default=".", help="项目目录路径（默认当前目录）")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()

    print(f"📁 初始化 Quarto 项目: {project_dir}")
    print()

    created, skipped = init_project(project_dir)

    if created:
        print("✅ 已创建:")
        for f in created:
            print(f"   - {f}")

    if skipped:
        print("⏭️  已跳过（文件已存在）:")
        for f in skipped:
            print(f"   - {f}")

    print()
    print("下一步:")
    print("  1. 编辑 data.yml 填写数据")
    print("  2. 在 src/ 下创建 .qmd 模板")
    print("  3. 运行 ./render.sh 渲染")


if __name__ == "__main__":
    main()
