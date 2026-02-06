#!/usr/bin/env python3
"""
扫描 .assets/scripts/ 目录，生成 scripts.json 和 dependencies.json
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent.parent.parent / ".assets" / "scripts"
DATA_DIR = Path(__file__).parent.parent / "data"

# 类型映射
TYPE_MAP = {
    "docx": {"icon": "📄", "color": "#2563EB", "name": "Word 文档"},
    "xlsx": {"icon": "📊", "color": "#059669", "name": "Excel 表格"},
    "csv": {"icon": "📋", "color": "#0891B2", "name": "CSV 数据"},
    "md": {"icon": "📝", "color": "#7C3AED", "name": "Markdown"},
    "pptx": {"icon": "📽️", "color": "#DC2626", "name": "PowerPoint"},
    "pdf": {"icon": "📕", "color": "#B91C1C", "name": "PDF 文档"},
    "yabai": {"icon": "🪟", "color": "#F59E0B", "name": "窗口管理"},
    "clashx": {"icon": "🌐", "color": "#6366F1", "name": "代理控制"},
    "file": {"icon": "📁", "color": "#8B5CF6", "name": "文件操作"},
    "folder": {"icon": "📂", "color": "#A855F7", "name": "文件夹操作"},
    "app": {"icon": "🚀", "color": "#EC4899", "name": "应用启动"},
    "sys": {"icon": "⚙️", "color": "#64748B", "name": "系统工具"},
    "display": {"icon": "🖥️", "color": "#0EA5E9", "name": "显示设置"},
    "gantt": {"icon": "📅", "color": "#14B8A6", "name": "甘特图"},
    "quarto": {"icon": "📚", "color": "#F97316", "name": "报告构建"},
}

# 功能映射
FUNCTION_MAP = {
    "convert": {"icon": "🔄", "color": "#3B82F6", "name": "格式转换", "patterns": ["_to_", "_from_"]},
    "format": {"icon": "✨", "color": "#8B5CF6", "name": "格式化", "patterns": ["_apply_", "_format", "_style", "_font"]},
    "analyze": {"icon": "🔍", "color": "#10B981", "name": "分析", "patterns": ["_extract", "_analyze", "_split", "_merge"]},
    "automation": {"icon": "⚡", "color": "#F59E0B", "name": "自动化", "patterns": ["yabai_", "clashx_", "app_", "sys_"]},
}

def extract_raycast_metadata(content: str) -> dict:
    """从脚本内容提取 Raycast 元数据"""
    metadata = {}
    patterns = {
        "title": r"@raycast\.title\s+(.+)",
        "description": r"@raycast\.description\s+(.+)",
        "mode": r"@raycast\.mode\s+(\w+)",
        "icon": r"@raycast\.icon\s+(.+)",
        "packageName": r"@raycast\.packageName\s+(.+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, content)
        if match:
            metadata[key] = match.group(1).strip()
    return metadata

def extract_imports(content: str) -> list:
    """提取 Python 导入"""
    imports = []
    # from xxx import ...
    for match in re.finditer(r"from\s+([\w.]+)\s+import", content):
        imports.append(match.group(1))
    # import xxx
    for match in re.finditer(r"^import\s+([\w.]+)", content, re.MULTILINE):
        imports.append(match.group(1))
    return imports

def extract_shell_sources(content: str) -> list:
    """提取 Shell source 依赖"""
    sources = []
    for match in re.finditer(r'source\s+["\']?([^"\';\s]+)', content):
        sources.append(match.group(1))
    return sources

def get_script_type(filename: str) -> str:
    """根据文件名前缀判断类型"""
    for prefix in TYPE_MAP.keys():
        if filename.startswith(prefix + "_") or filename.startswith(prefix + "."):
            return prefix
    return "other"

def get_script_function(filename: str) -> str:
    """根据文件名判断功能"""
    for func, info in FUNCTION_MAP.items():
        for pattern in info["patterns"]:
            if pattern in filename:
                return func
    return "other"

def scan_scripts():
    """扫描所有脚本"""
    scripts = []
    dependencies = {"scripts": {}, "modules": {}}

    if not SCRIPTS_DIR.exists():
        print(f"❌ 脚本目录不存在: {SCRIPTS_DIR}")
        return scripts, dependencies

    # 获取目录下所有脚本文件名（用于判断本地依赖）
    local_scripts = set()
    for file_path in SCRIPTS_DIR.iterdir():
        if file_path.suffix in [".py", ".sh", ".zsh"]:
            # 记录不带扩展名的名称
            local_scripts.add(file_path.stem)
            local_scripts.add(file_path.name)

    for file_path in sorted(SCRIPTS_DIR.iterdir()):
        if file_path.is_dir():
            continue
        if file_path.suffix not in [".py", ".sh", ".zsh"]:
            continue
        if file_path.name.startswith("_") or file_path.name.startswith("."):
            continue

        filename = file_path.name
        content = file_path.read_text(encoding="utf-8", errors="ignore")

        # 基本信息
        script_type = get_script_type(filename)
        script_func = get_script_function(filename)
        is_raycast = "@raycast" in content

        # 元数据
        metadata = extract_raycast_metadata(content) if is_raycast else {}

        # 依赖
        if file_path.suffix == ".py":
            imports = extract_imports(content)
        else:
            imports = extract_shell_sources(content)

        # 区分本地依赖和外部依赖
        local_imports = []  # 本地脚本依赖
        external_imports = []  # 外部模块依赖
        for imp in imports:
            # 取模块名（去掉子模块）
            mod_name = imp.split(".")[0]
            if mod_name in local_scripts:
                local_imports.append(mod_name)
            else:
                external_imports.append(mod_name)

        # 统计
        lines = len(content.splitlines())
        size = file_path.stat().st_size

        script_info = {
            "id": filename,
            "name": filename,
            "title": metadata.get("title", filename.replace("_", "-").replace(".py", "").replace(".sh", "")),
            "description": metadata.get("description", ""),
            "type": script_type,
            "function": script_func,
            "platform": "raycast" if is_raycast else "cli",
            "icon": metadata.get("icon") or TYPE_MAP.get(script_type, {}).get("icon", "📜"),
            "mode": metadata.get("mode", ""),
            "lines": lines,
            "size": size,
            "path": str(file_path),
            "imports": imports,
            "localImports": local_imports,  # 本地依赖（Link Out）
            "externalImports": external_imports,  # 外部依赖
            "tags": [script_type, script_func, "raycast" if is_raycast else "cli"],
        }
        scripts.append(script_info)

        # 依赖关系
        dependencies["scripts"][filename] = imports

    # 计算反向依赖（Link In）- 谁依赖了这个脚本
    for script in scripts:
        script_stem = Path(script["name"]).stem  # 不带扩展名
        linked_by = []
        for other in scripts:
            if other["id"] == script["id"]:
                continue
            if script_stem in other.get("localImports", []):
                linked_by.append(other["id"])
        script["linkedBy"] = linked_by  # 被谁依赖（Link In）

    return scripts, dependencies

def generate_stats(scripts: list) -> dict:
    """生成统计信息"""
    stats = {
        "total": len(scripts),
        "by_type": {},
        "by_function": {},
        "by_platform": {},
    }

    for s in scripts:
        # 按类型
        t = s["type"]
        stats["by_type"][t] = stats["by_type"].get(t, 0) + 1
        # 按功能
        f = s["function"]
        stats["by_function"][f] = stats["by_function"].get(f, 0) + 1
        # 按平台
        p = s["platform"]
        stats["by_platform"][p] = stats["by_platform"].get(p, 0) + 1

    return stats

def main():
    print("🔍 扫描脚本目录...")
    scripts, dependencies = scan_scripts()

    print(f"📊 找到 {len(scripts)} 个脚本")

    stats = generate_stats(scripts)

    # 生成 scripts.json
    data = {
        "generated_at": datetime.now().isoformat(),
        "stats": stats,
        "types": TYPE_MAP,
        "functions": FUNCTION_MAP,
        "scripts": scripts,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    scripts_json = DATA_DIR / "scripts.json"
    with open(scripts_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成: {scripts_json}")

    # 生成 dependencies.json
    deps_json = DATA_DIR / "dependencies.json"
    with open(deps_json, "w", encoding="utf-8") as f:
        json.dump(dependencies, f, ensure_ascii=False, indent=2)
    print(f"✅ 已生成: {deps_json}")

    # 打印统计
    print("\n📈 统计:")
    print(f"  按类型: {stats['by_type']}")
    print(f"  按功能: {stats['by_function']}")
    print(f"  按平台: {stats['by_platform']}")

if __name__ == "__main__":
    main()
