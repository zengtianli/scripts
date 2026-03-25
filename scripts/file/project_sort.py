#!/usr/bin/env python3
"""按项目名前缀归组文件到子目录。

适用于已经统一命名为「项目名-内容描述-日期.ext」格式的文件。
提取第一个「-」之前的部分作为项目名，同项目 ≥2 个文件时建子目录。

用法:
    python3 project_sort.py                    # 整理所有分类目录
    python3 project_sort.py --dry-run          # 预览模式
    python3 project_sort.py --dir ~/Downloads/文档  # 指定目录
    python3 project_sort.py --min 3            # 至少3个同项目才建目录
"""

import argparse
import logging
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
CONFIG_FILE = SCRIPT_DIR / "downloads_organizer.yaml"

# 这些目录本身就是分类目录，不要把它们当文件处理
SKIP_DIRS = {"_历史版本", "_backup", "_其他文件"}

# 忽略的文件前缀
IGNORE_PREFIXES = ("~$", ".", "_rename")


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("project_sort")
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)
    return logger


def extract_project_name(filename: str) -> str | None:
    """从文件名提取项目名（第一个 - 之前的部分）。

    返回 None 表示文件名不含 - 或项目名太短（≤1字符）。
    """
    # 跳过隐藏文件和临时文件
    if any(filename.startswith(p) for p in IGNORE_PREFIXES):
        return None

    idx = filename.find("-")
    if idx <= 1:
        return None

    project = filename[:idx].strip()
    # 过滤掉纯数字前缀（如 20260310-xxx）
    if project.isdigit():
        return None

    return project


def scan_and_group(directory: Path, logger: logging.Logger) -> dict[str, list[Path]]:
    """扫描目录，按项目名分组。只处理一级文件。"""
    groups = defaultdict(list)

    if not directory.exists():
        logger.warning("目录不存在: %s", directory)
        return groups

    for item in sorted(directory.iterdir()):
        if not item.is_file():
            continue
        project = extract_project_name(item.name)
        if project:
            groups[project].append(item)

    return dict(groups)


def sort_files(
    directory: Path,
    groups: dict[str, list[Path]],
    min_count: int,
    dry_run: bool,
    logger: logging.Logger,
) -> tuple[int, int]:
    """将同项目文件移入子目录。返回 (moved, skipped)。"""
    moved = 0
    skipped = 0

    for project, files in sorted(groups.items()):
        if len(files) < min_count:
            skipped += len(files)
            continue

        dest_dir = directory / project
        if not dry_run:
            dest_dir.mkdir(exist_ok=True)

        for f in files:
            dest = dest_dir / f.name
            if f.parent == dest_dir:
                skipped += 1
                continue

            if dry_run:
                logger.info("[预览] %s → %s/", f.name, project)
            else:
                if dest.exists():
                    # 文件名冲突加序号
                    stem, ext = f.stem, f.suffix
                    counter = 1
                    while dest.exists():
                        dest = dest_dir / f"{stem} ({counter}){ext}"
                        counter += 1
                shutil.move(str(f), str(dest))
                logger.info("[移动] %s → %s/", f.name, project)
            moved += 1

    return moved, skipped


def main():
    parser = argparse.ArgumentParser(description="按项目名前缀归组文件到子目录")
    parser.add_argument("--dry-run", action="store_true", help="预览模式，只打印不移动")
    parser.add_argument("--dir", help="指定单个目录（默认扫描所有分类目录）")
    parser.add_argument("--min", type=int, default=2, help="至少 N 个同项目文件才建子目录（默认 2）")
    args = parser.parse_args()

    logger = setup_logging()

    # 确定要扫描的目录（只扫描分类目录，不扫描项目文件夹）
    if args.dir:
        scan_dirs = [Path(args.dir).expanduser()]
    else:
        smart_cfg = SCRIPT_DIR / "smart_rename_config.yaml"
        with open(smart_cfg, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        scan_dirs = [Path(d).expanduser() for d in config["scan_dirs"]]

    if args.dry_run:
        logger.info("=== 预览模式 ===")

    total_moved = 0
    total_skipped = 0

    for d in scan_dirs:
        groups = scan_and_group(d, logger)
        if not groups:
            continue

        # 统计有多少组 ≥ min_count
        qualified = {k: v for k, v in groups.items() if len(v) >= args.min}
        if not qualified:
            continue

        logger.info(
            "扫描: %s （%d 个项目组, %d 个文件）", d.name, len(qualified), sum(len(v) for v in qualified.values())
        )

        moved, skipped = sort_files(d, groups, args.min, args.dry_run, logger)
        total_moved += moved
        total_skipped += skipped

    mode = "预览" if args.dry_run else "整理"
    logger.info("=== %s完成: 移动 %d 个文件, 跳过 %d 个 ===", mode, total_moved, total_skipped)


if __name__ == "__main__":
    main()
