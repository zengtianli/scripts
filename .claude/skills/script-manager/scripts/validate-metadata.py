#!/usr/bin/env python3
"""
Raycast 元数据验证工具

用途：验证所有 Raycast wrapper 的元数据完整性
检查：必需字段、格式正确性、文件权限
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional

# 颜色定义
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_info(msg: str):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.NC}")

def print_success(msg: str):
    print(f"{Colors.GREEN}✅ {msg}{Colors.NC}")

def print_error(msg: str):
    print(f"{Colors.RED}❌ {msg}{Colors.NC}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.NC}")

# ============================================================
# 元数据验证
# ============================================================

REQUIRED_FIELDS = [
    'schemaVersion',
    'title',
    'description',
    'mode',
    'icon',
    'packageName'
]

VALID_MODES = ['silent', 'compact', 'fullOutput']

def extract_metadata(file_path: Path) -> Dict[str, str]:
    """提取 Raycast 元数据"""
    metadata = {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取 @raycast.* 注释
        for line in content.split('\n'):
            if line.startswith('# @raycast.'):
                match = re.match(r'# @raycast\.(\w+)\s+(.+)', line)
                if match:
                    key = match.group(1)
                    value = match.group(2).strip()
                    metadata[key] = value

    except Exception as e:
        print_error(f"读取文件失败: {file_path.name} - {str(e)}")

    return metadata

def validate_metadata(file_path: Path, metadata: Dict[str, str]) -> List[str]:
    """验证元数据完整性"""
    errors = []

    # 检查必需字段
    for field in REQUIRED_FIELDS:
        if field not in metadata:
            errors.append(f"缺少必需字段: @raycast.{field}")

    # 检查 mode 值
    if 'mode' in metadata:
        mode = metadata['mode']
        if mode not in VALID_MODES:
            errors.append(f"无效的 mode 值: {mode} (应为 {', '.join(VALID_MODES)} 之一)")

    # 检查 schemaVersion
    if 'schemaVersion' in metadata:
        version = metadata['schemaVersion']
        if version != '1':
            errors.append(f"无效的 schemaVersion: {version} (应为 1)")

    # 检查文件权限
    if not os.access(file_path, os.X_OK):
        errors.append("文件没有执行权限")

    # 检查是否调用了实际脚本
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if 'run_python' not in content and 'run_shell' not in content and 'run_streamlit' not in content:
            errors.append("未找到脚本调用 (run_python/run_shell/run_streamlit)")

    except Exception as e:
        errors.append(f"读取文件内容失败: {str(e)}")

    return errors

def check_script_exists(file_path: Path) -> Optional[str]:
    """检查被调用的脚本是否存在"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取脚本路径
        match = re.search(r'run_(?:python|shell|streamlit)\s+"([^"]+)"', content)
        if match:
            script_relative_path = match.group(1)
            # 构建完整路径
            project_root = file_path.parent.parent.parent
            script_path = project_root / 'scripts' / script_relative_path

            if not script_path.exists():
                return f"被调用的脚本不存在: {script_relative_path}"

    except Exception as e:
        return f"检查脚本存在性失败: {str(e)}"

    return None

# ============================================================
# 扫描和报告
# ============================================================

def scan_wrappers(raycast_dir: Path) -> Dict[str, List[str]]:
    """扫描所有 Raycast wrapper"""
    results = {}

    if not raycast_dir.exists():
        print_error(f"Raycast 目录不存在: {raycast_dir}")
        return results

    # 遍历所有 .sh 文件
    for wrapper_path in raycast_dir.glob('*.sh'):
        # 跳过 _archived 目录
        if '_archived' in str(wrapper_path):
            continue

        # 提取元数据
        metadata = extract_metadata(wrapper_path)

        # 验证元数据
        errors = validate_metadata(wrapper_path, metadata)

        # 检查脚本存在性
        script_error = check_script_exists(wrapper_path)
        if script_error:
            errors.append(script_error)

        if errors:
            results[wrapper_path.name] = errors

    return results

def print_report(results: Dict[str, List[str]]):
    """打印验证报告"""
    print("")
    print("=" * 50)
    print("  Raycast 元数据验证报告")
    print("=" * 50)
    print("")

    if not results:
        print_success("所有 wrapper 元数据完整且正确")
        return

    print_warning(f"发现 {len(results)} 个文件存在问题：")
    print("")

    for file_name, errors in sorted(results.items()):
        print(f"📄 {file_name}")
        for error in errors:
            print(f"   • {error}")
        print("")

    print("=" * 50)
    print_info(f"总计: {len(results)} 个文件需要修复")

# ============================================================
# 主函数
# ============================================================

def main():
    # 获取项目根目录
    script_dir = Path(__file__).parent
    skill_dir = script_dir.parent
    project_root = skill_dir.parent.parent.parent
    raycast_dir = project_root / 'raycast' / 'commands'

    print_info(f"扫描目录: {raycast_dir}")

    # 扫描 wrapper
    results = scan_wrappers(raycast_dir)

    # 打印报告
    print_report(results)

    # 返回退出码
    if results:
        exit(1)
    else:
        exit(0)

if __name__ == '__main__':
    main()
