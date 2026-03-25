#!/usr/bin/env python3
"""
项目健康检查工具
检查：断裂链接、缺失依赖、无效路径、import 引用

使用方式：
    python3 lib/tools/health_check.py
"""

import ast
import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
LIB_DIR = PROJECT_ROOT / "lib"
PROJECTS_DIR = PROJECT_ROOT / "projects"

# lib/ 下可用的模块名
LIB_MODULES = {
    "display", "finder", "clipboard", "progress", "usage_log",
    "file_ops", "env", "docx_utils", "common_utils", "common",
    "excel_ops",
}


class HealthChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def check_broken_symlinks(self):
        """检查断裂软链接"""
        count = 0
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # 跳过 .git 和 node_modules
            dirs[:] = [d for d in dirs if d not in ('.git', 'node_modules', '.oa', '__pycache__')]
            for name in files:
                filepath = Path(root) / name
                if filepath.is_symlink() and not filepath.exists():
                    self.errors.append(f"断裂链接: {filepath.relative_to(PROJECT_ROOT)}")
                    count += 1
        return count

    def check_python_imports(self):
        """检查 Python 脚本的 import 是否能解析到 lib/ 中的模块"""
        count = 0
        for script in sorted(SCRIPTS_DIR.rglob("*.py")):
            try:
                content = script.read_text(encoding="utf-8")
            except Exception:
                continue

            # 查找 sys.path.insert 行，确认是否引用了 lib/
            uses_lib = "parent.parent" in content and '"lib"' in content

            if not uses_lib:
                continue

            # 解析 from X import Y 语句
            for match in re.finditer(r'^from\s+(\w+)\s+import', content, re.MULTILINE):
                module = match.group(1)
                # 跳过标准库和第三方库
                if module in LIB_MODULES:
                    # 检查模块文件是否存在
                    mod_file = LIB_DIR / f"{module}.py"
                    if not mod_file.exists():
                        self.errors.append(
                            f"{script.name}: import '{module}' 但 lib/{module}.py 不存在"
                        )
                        count += 1
        return count

    def check_shell_sources(self):
        """检查 Shell 脚本的 source 引用"""
        count = 0
        for script in sorted(SCRIPTS_DIR.rglob("*.sh")):
            try:
                content = script.read_text(encoding="utf-8")
            except Exception:
                continue

            for match in re.finditer(r'source\s+"[^"]*?/lib/(\S+)"', content):
                lib_file = match.group(1)
                if not (LIB_DIR / lib_file).exists():
                    self.errors.append(
                        f"{script.name}: source lib/{lib_file} 但文件不存在"
                    )
                    count += 1
        return count

    def check_hardcoded_paths(self):
        """检查硬编码路径"""
        count = 0
        patterns = [
            r'/Users/tianli/miniforge3/bin/python3',
            r'/Users/tianli/useful_scripts/execute',
        ]
        for script in sorted(SCRIPTS_DIR.rglob("*")):
            if script.suffix not in ('.py', '.sh'):
                continue
            try:
                content = script.read_text(encoding="utf-8")
            except Exception:
                continue
            for pattern in patterns:
                if pattern in content:
                    self.warnings.append(
                        f"{script.name}: 包含硬编码路径 '{pattern}'"
                    )
                    count += 1
        # 也检查 lib/
        for lib_file in sorted(LIB_DIR.glob("*")):
            if lib_file.suffix not in ('.py', '.sh'):
                continue
            try:
                content = lib_file.read_text(encoding="utf-8")
            except Exception:
                continue
            for pattern in patterns:
                if pattern in content:
                    self.warnings.append(
                        f"lib/{lib_file.name}: 包含硬编码路径 '{pattern}'"
                    )
                    count += 1
        return count

    def check_shebang(self):
        """检查 shebang 是否使用 env"""
        count = 0
        for script in sorted(SCRIPTS_DIR.rglob("*.py")):
            try:
                first_line = script.read_text(encoding="utf-8").split('\n')[0]
            except Exception:
                continue
            if first_line.startswith('#!') and '/env ' not in first_line:
                self.warnings.append(
                    f"{script.name}: shebang 未使用 env ({first_line})"
                )
                count += 1
        return count

    def check_import_syntax(self):
        """尝试语法解析所有 Python 脚本"""
        count = 0
        for script in sorted(SCRIPTS_DIR.rglob("*.py")):
            try:
                content = script.read_text(encoding="utf-8")
                ast.parse(content)
            except SyntaxError as e:
                self.errors.append(f"{script.name}: 语法错误 - {e}")
                count += 1
            except Exception:
                pass
        return count

    def check_projects_shebangs(self):
        """检查 projects/ 下 Python shebang 规范"""
        count = 0
        if not PROJECTS_DIR.exists():
            return count
        for script in sorted(PROJECTS_DIR.rglob("*.py")):
            try:
                first_line = script.read_text(encoding="utf-8").split('\n')[0]
            except Exception:
                continue
            if first_line.startswith('#!') and '/env ' not in first_line:
                self.warnings.append(
                    f"projects/{script.relative_to(PROJECTS_DIR)}: shebang 未使用 env ({first_line})"
                )
                count += 1
        return count

    def check_projects_hardcoded_paths(self):
        """检查 projects/ 下硬编码路径"""
        count = 0
        if not PROJECTS_DIR.exists():
            return count
        patterns = [
            '/Users/tianli/miniforge3',
            '/Users/tianli/useful_scripts/execute',
        ]
        for script in sorted(PROJECTS_DIR.rglob("*")):
            if script.suffix not in ('.py', '.sh'):
                continue
            if not script.is_file():
                continue
            try:
                content = script.read_text(encoding="utf-8")
            except Exception:
                continue
            for pattern in patterns:
                if pattern in content:
                    self.warnings.append(
                        f"projects/{script.relative_to(PROJECTS_DIR)}: 包含硬编码路径 '{pattern}'"
                    )
                    count += 1
        return count

    def check_projects_imports(self):
        """检查 projects/ 下 Python 脚本的 import 引用有效性"""
        count = 0
        if not PROJECTS_DIR.exists():
            return count
        # 检查 risk_data/ 下的脚本
        risk_dir = PROJECTS_DIR / "risk_data"
        if risk_dir.exists():
            for script in sorted(risk_dir.glob("*.py")):
                try:
                    content = script.read_text(encoding="utf-8")
                    ast.parse(content)
                except SyntaxError as e:
                    self.errors.append(
                        f"projects/risk_data/{script.name}: 语法错误 - {e}"
                    )
                    count += 1
                except Exception:
                    pass
        # 检查 qgis/ 下的脚本
        for subdir in ['pipeline', 'tools', '_util']:
            qgis_dir = PROJECTS_DIR / "qgis" / subdir
            if not qgis_dir.exists():
                continue
            for script in sorted(qgis_dir.glob("*.py")):
                try:
                    content = script.read_text(encoding="utf-8")
                    ast.parse(content)
                except SyntaxError as e:
                    self.errors.append(
                        f"projects/qgis/{subdir}/{script.name}: 语法错误 - {e}"
                    )
                    count += 1
                except Exception:
                    pass
        return count

    def run(self):
        """运行所有检查"""
        print("=" * 60)
        print("项目健康检查")
        print("=" * 60)

        checks = [
            ("断裂链接", self.check_broken_symlinks),
            ("Python import", self.check_python_imports),
            ("Shell source", self.check_shell_sources),
            ("硬编码路径", self.check_hardcoded_paths),
            ("Shebang 规范", self.check_shebang),
            ("Python 语法", self.check_import_syntax),
            ("Projects shebang", self.check_projects_shebangs),
            ("Projects 硬编码路径", self.check_projects_hardcoded_paths),
            ("Projects import", self.check_projects_imports),
        ]

        for name, check_fn in checks:
            count = check_fn()
            status = "PASS" if count == 0 else f"FAIL ({count})"
            print(f"  [{status}] {name}")

        if self.errors:
            print(f"\n错误 ({len(self.errors)}):")
            for e in self.errors:
                print(f"  ❌ {e}")

        if self.warnings:
            print(f"\n警告 ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  ⚠️  {w}")

        total = len(self.errors) + len(self.warnings)
        if total == 0:
            print("\n✅ 所有检查通过")
        else:
            print(f"\n共 {len(self.errors)} 个错误, {len(self.warnings)} 个警告")

        return len(self.errors)


if __name__ == "__main__":
    checker = HealthChecker()
    exit_code = checker.run()
    sys.exit(1 if exit_code > 0 else 0)
