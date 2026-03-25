#!/usr/bin/env python3
"""
删除 Markdown 文件中所有 blockquote 行（> 开头）及其前后多余空行。

用途：标书 md_final/ 中包含评分引用、数据来源等 blockquote 标注，
生成 docx 前需要去掉这些标注，只保留正文内容。
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_error, show_info, show_success
from file_ops import show_version_info

SCRIPT_NAME = "md_strip_blockquote"
SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2026-03-14"


def strip_blockquotes(text: str) -> str:
    """删除所有 blockquote 行，并清理残留的连续空行"""
    lines = text.split("\n")
    result = []
    in_code = False

    for line in lines:
        stripped = line.strip()

        # 跟踪代码块
        if stripped.startswith("```"):
            in_code = not in_code
            result.append(line)
            continue

        # 代码块内不处理
        if in_code:
            result.append(line)
            continue

        # 跳过 blockquote 行
        if stripped.startswith(">"):
            continue

        result.append(line)

    # 清理连续空行（最多保留 1 个）
    cleaned = []
    prev_empty = False
    for line in result:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        cleaned.append(line)
        prev_empty = is_empty

    return "\n".join(cleaned)


def count_blockquotes(text: str) -> int:
    """统计 blockquote 行数（排除代码块内）"""
    lines = text.split("\n")
    count = 0
    in_code = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if stripped.startswith(">"):
            count += 1
    return count


def process_file(filepath: Path, do_fix: bool, output_dir: Path | None) -> dict:
    """处理单个文件"""
    text = filepath.read_text(encoding="utf-8")
    bq_count = count_blockquotes(text)

    if bq_count > 0:
        print(f"  {filepath.name}: {bq_count} 行 blockquote")
    else:
        print(f"  {filepath.name}: 无 blockquote")

    if do_fix and bq_count > 0:
        fixed_text = strip_blockquotes(text)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / filepath.name
        else:
            out_path = filepath

        out_path.write_text(fixed_text, encoding="utf-8")
        show_success(f"已删除 {bq_count} 行 → {out_path}")

    return {"file": filepath.name, "blockquotes": bq_count}


def main():
    parser = argparse.ArgumentParser(
        description="删除 Markdown 文件中所有 blockquote（> 开头的行）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s md_final/                            检查模式（只统计）
  %(prog)s md_final/ --fix                      删除（覆盖原文件）
  %(prog)s md_final/ --fix --output-dir md_out/ 删除（输出到新目录）
""",
    )
    parser.add_argument("input", help="MD 文件或目录路径")
    parser.add_argument("--fix", action="store_true", help="执行删除")
    parser.add_argument("--output-dir", help="输出目录（默认覆盖原文件）")
    parser.add_argument("--version", action="store_true", help="显示版本信息")

    args = parser.parse_args()

    if args.version:
        show_version_info(SCRIPT_NAME, SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)
        return

    input_path = Path(args.input)
    if not input_path.exists():
        show_error(f"路径不存在: {input_path}")
        sys.exit(1)

    if input_path.is_dir():
        md_files = sorted(input_path.glob("*.md"))
        if not md_files:
            show_error(f"目录中没有 .md 文件: {input_path}")
            sys.exit(1)
        show_info(f"发现 {len(md_files)} 个 MD 文件")
    else:
        md_files = [input_path]

    output_dir = Path(args.output_dir) if args.output_dir else None

    all_stats = []
    for f in md_files:
        stats = process_file(f, args.fix, output_dir)
        all_stats.append(stats)

    total_bq = sum(s["blockquotes"] for s in all_stats)
    files_with_bq = sum(1 for s in all_stats if s["blockquotes"] > 0)

    if len(all_stats) > 1:
        print(f"\n合计: {total_bq} 行 blockquote（{files_with_bq}/{len(all_stats)} 个文件）")

    if total_bq > 0 and not args.fix:
        print("\n使用 --fix 执行删除")
        sys.exit(1)


if __name__ == "__main__":
    main()
