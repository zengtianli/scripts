#!/usr/bin/env python3
"""扫描指定目录，为每个包含二进制文件的子目录生成 _files.md 清单。"""

import argparse
import os
from datetime import datetime
from pathlib import Path

# 二进制文件扩展名
BINARY_EXTENSIONS = {
    ".docx", ".doc", ".pdf", ".xlsx", ".xls", ".pptx",
    ".dwg", ".gdb",
    ".m4v", ".mp4", ".avi",
    ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp",
    ".zip", ".rar", ".7z",
    ".shp", ".dbf", ".shx", ".prj", ".cpg",
}

# 分类规则
CATEGORIES = {
    "报告文档": {".docx", ".doc", ".pdf", ".pptx"},
    "数据文件": {".xlsx", ".xls", ".csv"},
    "图片/媒体": {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".m4v", ".mp4", ".avi"},
    "GIS/CAD": {".dwg", ".gdb", ".shp", ".dbf", ".shx", ".prj", ".cpg"},
    "压缩包": {".zip", ".rar", ".7z"},
}

# 跳过的目录名
SKIP_DIRS = {".git", "_trash"}

MANIFEST_NAME = "_files.md"


def format_size(size_bytes: int) -> str:
    """格式化文件大小。"""
    if size_bytes < 1024:
        return "1 KB"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes // 1024} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        mb = size_bytes / (1024 * 1024)
        return f"{mb:.1f} MB"
    else:
        gb = size_bytes / (1024 * 1024 * 1024)
        return f"{gb:.1f} GB"


def format_time(timestamp: float) -> str:
    """格式化修改时间为 YYYY-MM-DD。"""
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")


def classify_file(ext: str) -> str | None:
    """根据扩展名返回分类名，未匹配返回 None。"""
    ext_lower = ext.lower()
    for category, extensions in CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return None


def should_skip(path: Path) -> bool:
    """判断路径是否在需要跳过的目录下。"""
    return any(part in SKIP_DIRS for part in path.parts)


def scan_directory(target: Path, depth: int) -> dict[Path, list[Path]]:
    """扫描目标目录，按子目录分组收集二进制文件。

    返回 {子目录: [文件路径列表]} 的字典。
    """
    result: dict[Path, list[Path]] = {}

    for root, dirs, files in os.walk(target):
        root_path = Path(root)

        # 计算当前深度（相对于 target）
        rel = root_path.relative_to(target)
        current_depth = len(rel.parts) if str(rel) != "." else 0

        # 超过深度限制，不再递归
        if current_depth >= depth:
            dirs.clear()
            continue

        # 跳过特定目录（修改 dirs 列表以阻止 os.walk 递归进入）
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for fname in files:
            fpath = root_path / fname
            if fpath.name == MANIFEST_NAME:
                continue
            if fpath.suffix.lower() in BINARY_EXTENSIONS:
                # 确定该文件所属的「项目子目录」
                # 如果文件直接在 target 下，归属 target 自身
                if root_path == target:
                    group_dir = target
                else:
                    # 取相对于 target 的第一级子目录
                    group_dir = target / rel.parts[0]
                result.setdefault(group_dir, []).append(fpath)

    return result


def generate_manifest(directory: Path, files: list[Path]) -> str:
    """为一个目录生成 _files.md 内容。"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    dir_name = directory.name

    # 按分类归组
    categorized: dict[str, list[tuple[str, str, str]]] = {}
    for fpath in sorted(files, key=lambda p: p.name):
        cat = classify_file(fpath.suffix)
        if cat is None:
            continue
        stat = fpath.stat()
        entry = (fpath.name, format_size(stat.st_size), format_time(stat.st_mtime))
        categorized.setdefault(cat, []).append(entry)

    if not categorized:
        return ""

    lines = [
        f"# 文件清单 - {dir_name}",
        "",
        f"> 自动生成，勿手动编辑 | 更新时间: {now}",
    ]

    # 按固定顺序输出分类
    category_order = ["报告文档", "数据文件", "图片/媒体", "GIS/CAD", "压缩包"]
    for cat in category_order:
        entries = categorized.get(cat)
        if not entries:
            continue
        lines.append("")
        lines.append(f"## {cat}")
        lines.append("| 文件名 | 大小 | 修改时间 |")
        lines.append("|--------|------|----------|")
        for name, size, mtime in entries:
            lines.append(f"| {name} | {size} | {mtime} |")

    lines.append("")  # 末尾空行
    return "\n".join(lines)


def clean_manifests(target: Path, depth: int) -> int:
    """删除目标目录下已有的 _files.md 文件，返回删除数量。"""
    count = 0
    for root, dirs, files in os.walk(target):
        root_path = Path(root)
        rel = root_path.relative_to(target)
        current_depth = len(rel.parts) if str(rel) != "." else 0
        if current_depth >= depth:
            dirs.clear()
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        if MANIFEST_NAME in files:
            (root_path / MANIFEST_NAME).unlink()
            count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="扫描目录，生成二进制文件清单 _files.md")
    parser.add_argument("--target", required=True, type=str, help="目标目录路径")
    parser.add_argument("--depth", type=int, default=2, help="扫描深度（默认 2）")
    parser.add_argument("--clean", action="store_true", help="删除旧的 _files.md 后重新生成")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_dir():
        print(f"错误：目标目录不存在: {target}")
        raise SystemExit(1)

    depth = args.depth

    # 清理旧文件
    if args.clean:
        removed = clean_manifests(target, depth)
        if removed:
            print(f"已清理 {removed} 个旧 _files.md")

    # 扫描
    grouped = scan_directory(target, depth)
    if not grouped:
        print("未找到二进制文件。")
        return

    # 生成清单
    written = 0
    for directory, files in sorted(grouped.items()):
        content = generate_manifest(directory, files)
        if not content:
            continue
        manifest_path = directory / MANIFEST_NAME
        manifest_path.write_text(content, encoding="utf-8")
        written += 1
        print(f"已生成: {manifest_path}")

    print(f"共生成 {written} 个 _files.md")


if __name__ == "__main__":
    main()
