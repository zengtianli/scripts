#!/usr/bin/env python3
"""
将 MD 文件中的 ASCII art 代码块替换为 PNG 图片引用

根据 insert_config.json 配置，定位 MD 文件中特定章节下的 ASCII art
代码块（含 ┌┐└┘│─▼→ 等字符），替换为 ![caption](image_path)。

支持 check（报告）和 fix（替换）两种模式。
"""

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_error, show_info, show_success, show_warning
from file_ops import show_version_info

SCRIPT_NAME = "chart_insert"
SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2026-03-14"

# box-drawing 和流程图字符
ASCII_ART_CHARS = set("┌┐└┘│─├┤┬┴┼═║╔╗╚╝╠╣╦╩╬▼▲►◄→←↑↓█▏▎▍▌▋▊▉")


def is_ascii_art_block(lines: list[str]) -> bool:
    """判断代码块内容是否为 ASCII art 图表"""
    art_char_count = 0
    total_chars = 0
    for line in lines:
        for ch in line:
            total_chars += 1
            if ch in ASCII_ART_CHARS:
                art_char_count += 1
    # 至少包含 5 个图表字符
    return art_char_count >= 5


def find_code_blocks(text: str) -> list[dict]:
    """找到所有代码块及其位置信息"""
    lines = text.split("\n")
    blocks = []
    in_block = False
    block_start = -1
    block_lines = []

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            if not in_block:
                in_block = True
                block_start = i
                block_lines = []
            else:
                blocks.append(
                    {
                        "start": block_start,
                        "end": i,
                        "content_lines": block_lines,
                        "is_ascii_art": is_ascii_art_block(block_lines),
                    }
                )
                in_block = False
                block_start = -1
                block_lines = []
        elif in_block:
            block_lines.append(line)

    return blocks


def find_heading_for_block(lines: list[str], block_start: int) -> str | None:
    """向上查找代码块所在的最近标题编号（如 6.2.1）"""
    heading_re = re.compile(r"^#{1,4}\s+(\d+(?:\.\d+)*)\s")
    for i in range(block_start - 1, -1, -1):
        m = heading_re.match(lines[i].strip())
        if m:
            return m.group(1)
    return None


def check_insertions(md_dir: Path, config: dict) -> list[dict]:
    """检查哪些 ASCII art 代码块可以替换为图片"""
    mappings = config.get("mappings", [])
    _ = config.get("base_image_dir", "charts")
    issues = []

    for mapping in mappings:
        md_file = md_dir / mapping["file"]
        if not md_file.exists():
            issues.append(
                {
                    "file": mapping["file"],
                    "status": "missing",
                    "message": f"MD 文件不存在: {md_file}",
                }
            )
            continue

        text = md_file.read_text(encoding="utf-8")
        lines = text.split("\n")
        blocks = find_code_blocks(text)

        heading_match = mapping["heading_match"]
        image_file = mapping["image"]
        caption = mapping.get("caption", "")

        # 找匹配的 ASCII art 代码块
        found = False
        for block in blocks:
            if not block["is_ascii_art"]:
                continue
            heading = find_heading_for_block(lines, block["start"])
            if heading and heading == heading_match:
                # 检查是否已被替换（即代码块上方已有图片引用）
                if block["start"] > 0:
                    prev_line = lines[block["start"] - 1].strip()
                    if prev_line.startswith("![") and image_file in prev_line:
                        issues.append(
                            {
                                "file": mapping["file"],
                                "status": "already_done",
                                "line": block["start"] + 1,
                                "heading": heading_match,
                                "message": f"已替换为图片: {image_file}",
                            }
                        )
                        found = True
                        break

                issues.append(
                    {
                        "file": mapping["file"],
                        "status": "pending",
                        "line": block["start"] + 1,
                        "heading": heading_match,
                        "image": image_file,
                        "caption": caption,
                        "block_lines": len(block["content_lines"]),
                        "message": f"L{block['start'] + 1}-L{block['end'] + 1}: "
                        f"ASCII art ({len(block['content_lines'])}行) → {image_file}",
                    }
                )
                found = True
                break

        if not found:
            issues.append(
                {
                    "file": mapping["file"],
                    "status": "not_found",
                    "heading": heading_match,
                    "message": f"未找到 §{heading_match} 下的 ASCII art 代码块",
                }
            )

    return issues


def fix_insertions(md_dir: Path, config: dict, output_dir: Path | None = None) -> int:
    """执行替换：ASCII art → 图片引用"""
    mappings = config.get("mappings", [])
    base_image_dir = config.get("base_image_dir", "charts")
    fix_count = 0

    # 按文件分组
    file_mappings: dict[str, list] = {}
    for mapping in mappings:
        fname = mapping["file"]
        if fname not in file_mappings:
            file_mappings[fname] = []
        file_mappings[fname].append(mapping)

    for fname, fmappings in file_mappings.items():
        md_file = md_dir / fname
        if not md_file.exists():
            show_warning(f"跳过不存在的文件: {md_file}")
            continue

        text = md_file.read_text(encoding="utf-8")
        lines = text.split("\n")
        blocks = find_code_blocks(text)

        # 收集要替换的代码块（从后往前替换，避免行号偏移）
        replacements = []

        for mapping in fmappings:
            heading_match = mapping["heading_match"]
            image_path = f"{base_image_dir}/{mapping['image']}"
            caption = mapping.get("caption", "")

            for block in blocks:
                if not block["is_ascii_art"]:
                    continue
                heading = find_heading_for_block(lines, block["start"])
                if heading and heading == heading_match:
                    # 检查是否已替换
                    if block["start"] > 0:
                        prev_line = lines[block["start"] - 1].strip()
                        if prev_line.startswith("![") and mapping["image"] in prev_line:
                            show_info(f"  {fname} §{heading_match}: 已替换，跳过")
                            break

                    replacements.append(
                        {
                            "start": block["start"],
                            "end": block["end"],
                            "image_path": image_path,
                            "caption": caption,
                        }
                    )
                    break

        if not replacements:
            continue

        # 从后往前替换
        replacements.sort(key=lambda r: r["start"], reverse=True)
        for rep in replacements:
            image_line = f"![{rep['caption']}]({rep['image_path']})"
            # 替换代码块（包括 ``` 行）为图片引用
            lines[rep["start"] : rep["end"] + 1] = [image_line]
            fix_count += 1
            show_info(f"  {fname} L{rep['start'] + 1}: → {rep['image_path']}")

        # 写出
        out_file = (output_dir / fname) if output_dir else md_file
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text("\n".join(lines), encoding="utf-8")

    return fix_count


def format_report(issues: list[dict]) -> str:
    """格式化检查报告"""
    if not issues:
        return "没有找到需要处理的映射。"

    lines = ["=" * 60, "ASCII Art → PNG 替换检查报告", "=" * 60, ""]

    pending = [i for i in issues if i["status"] == "pending"]
    done = [i for i in issues if i["status"] == "already_done"]
    missing = [i for i in issues if i["status"] in ("not_found", "missing")]

    if pending:
        lines.append(f"待替换: {len(pending)} 处")
        for item in pending:
            lines.append(f"  [{item['file']}] {item['message']}")
        lines.append("")

    if done:
        lines.append(f"已完成: {len(done)} 处")
        for item in done:
            lines.append(f"  [{item['file']}] {item['message']}")
        lines.append("")

    if missing:
        lines.append(f"异常: {len(missing)} 处")
        for item in missing:
            lines.append(f"  [{item['file']}] {item['message']}")
        lines.append("")

    lines.append(f"总计: {len(pending)} 待替换, {len(done)} 已完成, {len(missing)} 异常")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="将 MD 中 ASCII art 代码块替换为 PNG 图片引用",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s md_fixed/ --config charts/insert_config.json
  %(prog)s md_fixed/ --config charts/insert_config.json --fix
  %(prog)s md_fixed/ --config charts/insert_config.json --fix --output-dir md_final/
""",
    )
    parser.add_argument("md_dir", nargs="?", help="MD 文件目录")
    parser.add_argument("--config", required=False, help="插入配置 JSON 文件")
    parser.add_argument("--fix", action="store_true", help="执行替换（默认只检查）")
    parser.add_argument("--output-dir", help="修复输出到新目录（不修改原文件）")
    parser.add_argument("--version", action="store_true", help="版本信息")

    args = parser.parse_args()

    if args.version:
        show_version_info(SCRIPT_NAME, SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)
        return

    if not args.md_dir or not args.config:
        parser.print_help()
        sys.exit(1)

    md_dir = Path(args.md_dir)
    config_path = Path(args.config)

    if not md_dir.is_dir():
        show_error(f"目录不存在: {md_dir}")
        sys.exit(1)
    if not config_path.exists():
        show_error(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    show_info(f"扫描目录: {md_dir}")
    show_info(f"配置文件: {config_path}")

    if args.fix:
        output_dir = Path(args.output_dir) if args.output_dir else None
        if output_dir and not output_dir.exists():
            # 先复制整个目录
            shutil.copytree(md_dir, output_dir)
            show_info(f"已复制到: {output_dir}")

        target_dir = output_dir or md_dir
        fix_count = fix_insertions(target_dir, config, output_dir=None)
        show_success(f"替换完成: {fix_count} 处")
    else:
        issues = check_insertions(md_dir, config)
        print(format_report(issues))


if __name__ == "__main__":
    main()
