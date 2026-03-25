#!/usr/bin/env python3
"""
索引同步工具
自动扫描 scripts/ 生成 _index/ 索引

使用方式：
    python3 lib/tools/sync_index.py          # 预览模式
    python3 lib/tools/sync_index.py --apply   # 执行同步
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
RAYCAST_DIR = PROJECT_ROOT / "raycast"
INDEX_DIR = PROJECT_ROOT / "_index"

# 文件名前缀 → raycast 子目录 & by-type 子目录
PREFIX_MAP = {
    "docx_": "docx",
    "xlsx_": "xlsx",
    "csv_": "csv",
    "md_": "md",
    "pptx_": "pptx",
    "yabai_": "yabai",
    "clashx_": "clashx",
    "display_": "system",
    "sys_": "system",
    "file_": "file",
    "folder_": "folder",
    "app_": "app",
}

# 文件名前缀 → by-function 分类
FUNCTION_MAP = {
    "docx_to_": "convert",
    "docx_from_": "convert",
    "xlsx_to_": "convert",
    "xlsx_from_": "convert",
    "csv_to_": "convert",
    "csv_from_": "convert",
    "pptx_to_": "convert",
    "md_to_": "convert",
    "docx_apply_": "format",
    "docx_text_": "format",
    "docx_zdwp_": "format",
    "pptx_apply_": "format",
    "pptx_font_": "format",
    "pptx_table_": "format",
    "pptx_text_": "format",
    "md_formatter": "format",
    "md_split_": "format",
    "md_merge": "format",
    "csv_merge_": "format",
    "xlsx_split": "format",
    "xlsx_lowercase": "format",
    "xlsx_merge": "format",
    "yabai_": "automation",
    "clashx_": "automation",
    "app_": "automation",
    "file_run": "automation",
    "display_": "automation",
    "sys_": "automation",
    "file_copy": "automation",
    "folder_": "automation",
    "md_docx_": "convert",
}


def get_type_category(name: str) -> str:
    """根据文件名前缀确定 by-type 分类"""
    for prefix, category in PREFIX_MAP.items():
        if name.startswith(prefix):
            return category
    return "other"


def get_function_category(name: str) -> str:
    """根据文件名确定 by-function 分类"""
    for prefix, category in sorted(FUNCTION_MAP.items(), key=lambda x: -len(x[0])):
        if name.startswith(prefix):
            return category
    return ""


def has_raycast_metadata(filepath: Path) -> bool:
    """检查脚本是否有 Raycast 元数据"""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return "@raycast." in content[:500]
    except Exception:
        return False


def get_platform(filepath: Path) -> str:
    """判断脚本平台：raycast 或 cli"""
    if has_raycast_metadata(filepath):
        return "raycast"
    return "cli"


def scan_scripts():
    """扫描所有脚本，返回分类信息"""
    scripts = []
    for f in sorted(SCRIPTS_DIR.iterdir()):
        if f.is_file() and f.suffix in (".py", ".sh"):
            name = f.stem
            scripts.append({
                "path": f,
                "name": f.name,
                "stem": name,
                "type_cat": get_type_category(name),
                "func_cat": get_function_category(name),
                "platform": get_platform(f),
            })
    return scripts


def compute_links(scripts):
    """计算需要创建的软链接"""
    links = []

    for s in scripts:
        target = s["path"]
        name = s["name"]

        # raycast/ 链接（仅 raycast 脚本）
        if s["platform"] == "raycast":
            link_path = RAYCAST_DIR / s["type_cat"] / name
            links.append((link_path, target))

        # _index/by-type/
        link_path = INDEX_DIR / "by-type" / s["type_cat"] / name
        links.append((link_path, target))

        # _index/by-platform/
        link_path = INDEX_DIR / "by-platform" / s["platform"] / name
        links.append((link_path, target))

        # _index/by-function/
        if s["func_cat"]:
            link_path = INDEX_DIR / "by-function" / s["func_cat"] / name
            links.append((link_path, target))

    return links


def get_existing_links(*dirs):
    """获取目录下所有现有软链接"""
    existing = set()
    for d in dirs:
        if d.exists():
            for f in d.rglob("*"):
                if f.is_symlink():
                    existing.add(f)
    return existing


def sync(apply=False):
    scripts = scan_scripts()
    desired_links = compute_links(scripts)

    # 计算需要的链接路径集合
    desired_paths = {link for link, _ in desired_links}

    # 获取现有链接
    existing = get_existing_links(RAYCAST_DIR, INDEX_DIR)

    # 需要删除的（存在但不在期望中）
    to_remove = existing - desired_paths

    # 需要创建的
    to_create = []
    to_update = []
    for link_path, target in desired_links:
        if link_path.is_symlink():
            current_target = link_path.resolve()
            if current_target != target.resolve():
                to_update.append((link_path, target))
        elif not link_path.exists():
            to_create.append((link_path, target))

    # 报告
    print(f"扫描到 {len(scripts)} 个脚本")
    print(f"期望链接: {len(desired_links)} 个")
    print(f"需要创建: {len(to_create)} 个")
    print(f"需要更新: {len(to_update)} 个")
    print(f"需要删除: {len(to_remove)} 个")
    print(f"已存在且正确: {len(desired_links) - len(to_create) - len(to_update)} 个")

    if to_create:
        print("\n--- 需要创建 ---")
        for link, target in sorted(to_create):
            rel = link.relative_to(PROJECT_ROOT)
            print(f"  + {rel} -> {target.name}")

    if to_update:
        print("\n--- 需要更新 ---")
        for link, target in sorted(to_update):
            rel = link.relative_to(PROJECT_ROOT)
            print(f"  ~ {rel} -> {target.name}")

    if to_remove:
        print("\n--- 需要删除 ---")
        for link in sorted(to_remove):
            rel = link.relative_to(PROJECT_ROOT)
            print(f"  - {rel}")

    if not apply:
        if to_create or to_update or to_remove:
            print("\n使用 --apply 执行同步")
        else:
            print("\n所有链接已是最新状态")
        return

    # 执行
    for link in to_remove:
        link.unlink()
        print(f"  删除: {link.relative_to(PROJECT_ROOT)}")

    for link, target in to_update:
        link.unlink()
        link.symlink_to(target)
        print(f"  更新: {link.relative_to(PROJECT_ROOT)}")

    for link, target in to_create:
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        print(f"  创建: {link.relative_to(PROJECT_ROOT)}")

    print("\n同步完成")


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    sync(apply=apply)
