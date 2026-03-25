#!/usr/bin/env python3
"""
表格标准化工具集

子命令:
  check    检查表名 + 引导段落（可自动插入占位）
  reorder  将表名从引导段落上方移到表格正上方

用法:
  python table_tools.py check md_final/
  python table_tools.py check md_final/ --fix
  python table_tools.py reorder md_final/
"""

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_error, show_info, show_success

# ── 共享常量 ──────────────────────────────────────────────────

TABLE_NAME_RE = re.compile(r"^表\d+")
TABLE_NAME_FULL_RE = re.compile(r"^表\d+-\d+\s")
TABLE_SEP_RE = re.compile(r"^\|[\s\-:]+(\|[\s\-:]+)+\|?\s*$")


# ── 共享工具 ──────────────────────────────────────────────────


def is_in_code_block(lines: list[str], line_idx: int) -> bool:
    """判断某行是否在代码块内"""
    in_code = False
    for i in range(line_idx):
        if lines[i].strip().startswith("```"):
            in_code = not in_code
    return in_code


def extract_chapter_num(filename: str) -> int:
    """从文件名提取章节号：01.md → 1"""
    m = re.match(r"(\d+)", filename)
    return int(m.group(1)) if m else 0


def find_tables(lines: list[str]) -> list[dict]:
    """找到所有表格（表头行 + 分隔行）"""
    tables = []
    for i in range(len(lines) - 1):
        if is_in_code_block(lines, i):
            continue
        stripped = lines[i].strip()
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if stripped.startswith("|") and stripped.endswith("|"):  # noqa: SIM102
            if TABLE_SEP_RE.match(next_stripped):
                if i > 0:
                    prev = lines[i - 1].strip()
                    if prev.startswith("|") and prev.endswith("|"):
                        continue
                tables.append({"header_line": i})
    return tables


def is_table_header(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def collect_md_files(input_path: Path) -> list[Path]:
    """收集 MD 文件列表"""
    if input_path.is_dir():
        md_files = sorted(input_path.glob("*.md"))
        md_files = [f for f in md_files if f.name != "merged.md" and not f.name.startswith("~")]
        if not md_files:
            show_error(f"目录中没有 .md 文件: {input_path}")
            sys.exit(1)
        show_info(f"发现 {len(md_files)} 个 MD 文件")
        return md_files
    return [input_path]


# ══════════════════════════════════════════════════════════════
# 子命令: check — 表名 + 引导段落检查
# ══════════════════════════════════════════════════════════════


def check_table_name(lines: list[str], table: dict) -> dict | None:
    """检查表格是否有表名"""
    header_line = table["header_line"]
    j = header_line - 1
    search_limit = max(0, header_line - 10)
    while j >= search_limit:
        stripped = lines[j].strip()
        if not stripped:
            j -= 1
            continue
        if stripped.startswith("#"):
            break
        if stripped.startswith("|") and stripped.endswith("|"):
            break
        if TABLE_NAME_RE.match(stripped):
            table["name_line"] = j
            table["has_name"] = True
            return None
        j -= 1

    table["has_name"] = False
    return {"type": "缺表名", "line": header_line + 1, "fixable": True}


def check_table_intro(lines: list[str], table: dict, min_chars: int = 80) -> dict | None:
    """检查表格前是否有充分的引导段落"""
    header_line = table["header_line"]
    name_line = table.get("name_line")
    best_intro = ""

    # 位置1：表名行与表头行之间
    if name_line is not None and header_line - name_line > 2:
        for j in range(name_line + 1, header_line):
            stripped = lines[j].strip()
            if not stripped or stripped.startswith("|") or stripped.startswith("#") or stripped.startswith(">"):
                continue
            clean = re.sub(r"[*#>\[\]`]", "", stripped)
            if len(clean) > len(best_intro):
                best_intro = clean

    # 位置2：表名行（或表头行）之上
    start = (name_line if name_line is not None else header_line) - 1
    j = start
    while j >= 0 and lines[j].strip() == "":
        j -= 1

    if j >= 0:
        stripped = lines[j].strip()
        if stripped.startswith(">"):
            k = j - 1
            while k >= 0 and (lines[k].strip().startswith(">") or lines[k].strip() == ""):
                k -= 1
            stripped = lines[k].strip() if k >= 0 else ""
        if not stripped.startswith("#") and not (stripped.startswith("|") and stripped.endswith("|")):
            clean = re.sub(r"[*#>\[\]`]", "", stripped)
            if len(clean) > len(best_intro):
                best_intro = clean

    if len(best_intro) == 0:
        return {"type": "缺引导段落", "line": header_line + 1, "intro_len": 0, "fixable": True}
    if len(best_intro) < min_chars:
        return {
            "type": "引导段落过短",
            "line": header_line + 1,
            "intro_len": len(best_intro),
            "intro_text": best_intro[:60],
            "min_chars": min_chars,
            "fixable": True,
        }
    return None


def fix_insert_table_names(text: str, chapter_num: int, min_intro_chars: int = 80) -> str:
    """在缺表名的表格前插入占位表名"""
    lines = text.split("\n")
    tables = find_tables(lines)
    insertions = []

    table_counter = 0
    for table in tables:
        table_counter += 1  # noqa: SIM113
        name_issue = check_table_name(lines, table)
        intro_issue = check_table_intro(lines, table, min_intro_chars)

        if name_issue:
            table_name = f"表{chapter_num}-{table_counter} [待命名]"
            insertions.append({"line": table["header_line"], "content": table_name, "type": "name"})

        if intro_issue:
            insert_before = table.get("name_line", table["header_line"])
            if name_issue:
                insert_before = table["header_line"]
            insertions.append({"line": insert_before, "content": "<!-- TABLE_NEEDS_INTRO -->", "type": "intro"})

    insertions.sort(key=lambda x: (-x["line"], x["type"] == "name"))

    for ins in insertions:
        idx = ins["line"]
        lines.insert(idx, "")
        lines.insert(idx, ins["content"])
        if idx > 0 and lines[idx - 1].strip() != "":
            lines.insert(idx, "")

    return "\n".join(lines)


def format_report(filepath: str, name_issues: list, intro_issues: list) -> str:
    """格式化检查报告"""
    parts = [f"文件: {filepath}", ""]
    total = 0

    if name_issues:
        parts.append(f"[缺表名] {len(name_issues)} 个表格")
        for item in name_issues:
            parts.append(f"  L{item['line']}: 表格无表名")
        total += len(name_issues)
    else:
        parts.append("[缺表名] 无问题")
    parts.append("")

    if intro_issues:
        parts.append(f"[缺引导段落] {len(intro_issues)} 个表格")
        for item in intro_issues:
            if item["type"] == "缺引导段落":
                parts.append(f"  L{item['line']}: 标题后直接跟表格")
            else:
                parts.append(
                    f"  L{item['line']}: 引导语仅{item['intro_len']}字"
                    f"（要求≥{item.get('min_chars', 80)}字）"
                    f' — "{item.get("intro_text", "")}"'
                )
        total += len(intro_issues)
    else:
        parts.append("[缺引导段落] 无问题")
    parts.append("")

    parts.append("─" * 40)
    parts.append(f"小计: {total} 个问题")
    return "\n".join(parts)


def check_process_file(filepath: Path, do_fix: bool, min_intro: int) -> dict:
    """处理单个文件的检查"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    chapter_num = extract_chapter_num(filepath.name)

    tables = find_tables(lines)
    if not tables:
        print(f"\n文件: {filepath}")
        print("  无表格，跳过\n")
        return {"total": 0, "name_missing": 0, "intro_missing": 0, "tables": 0, "file": str(filepath)}

    name_issues = []
    intro_issues = []

    table_counter = 0
    for table in tables:
        table_counter += 1  # noqa: SIM113
        ni = check_table_name(lines, table)
        if ni:
            name_issues.append(ni)
        ii = check_table_intro(lines, table, min_intro)
        if ii:
            intro_issues.append(ii)

    report = format_report(str(filepath), name_issues, intro_issues)
    print(f"\n{'─' * 3} 表格标准化检查 {'─' * 3}\n")
    print(report)

    total = len(name_issues) + len(intro_issues)
    if do_fix and total > 0:
        fixed_text = fix_insert_table_names(text, chapter_num, min_intro)
        filepath.write_text(fixed_text, encoding="utf-8")
        show_success(f"已修复并保存: {filepath}")

    return {
        "total": total,
        "name_missing": len(name_issues),
        "intro_missing": len(intro_issues),
        "tables": len(tables),
        "file": str(filepath),
    }


def cmd_check(args):
    """check 子命令入口"""
    input_path = Path(args.input)
    if not input_path.exists():
        show_error(f"路径不存在: {input_path}")
        sys.exit(1)

    md_files = collect_md_files(input_path)
    all_stats = []
    for f in md_files:
        stats = check_process_file(f, args.fix, args.min_intro)
        all_stats.append(stats)

    if len(all_stats) > 1:
        grand_total = sum(s["total"] for s in all_stats)
        grand_tables = sum(s["tables"] for s in all_stats)
        grand_names = sum(s["name_missing"] for s in all_stats)
        grand_intros = sum(s["intro_missing"] for s in all_stats)
        print(f"\n{'═' * 3} 全部文件汇总 {'═' * 3}")
        print(f"文件数: {len(all_stats)}")
        print(f"表格总数: {grand_tables}")
        print(f"缺表名: {grand_names}")
        print(f"缺引导段落: {grand_intros}")
        print(f"总问题: {grand_total}")
        print("═" * 40)

    total = sum(s["total"] for s in all_stats)
    if total > 0 and not args.fix:
        sys.exit(1)


# ══════════════════════════════════════════════════════════════
# 子命令: reorder — 表名位置修复
# ══════════════════════════════════════════════════════════════


def reorder_fix_file(filepath: Path) -> int:
    """修复单个文件中表名位置，返回修复数量"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    fixes = 0

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()
        if not TABLE_NAME_FULL_RE.match(stripped):
            i += 1
            continue

        name_line_idx = i
        name_line = lines[i]

        j = i + 1
        intro_lines = []
        found_table = False

        while j < len(lines):
            jstripped = lines[j].strip()
            if jstripped == "":
                j += 1
                continue
            if is_table_header(jstripped):
                if j + 1 < len(lines) and TABLE_SEP_RE.match(lines[j + 1].strip()):
                    found_table = True
                    table_header_idx = j
                    break
                else:
                    intro_lines.append(lines[j])
                    j += 1
                    continue
            if jstripped.startswith("#"):
                break
            intro_lines.append(lines[j])
            j += 1

        if not found_table:
            i += 1
            continue

        if not intro_lines:
            lines[name_line_idx : table_header_idx + 1] = [name_line, lines[table_header_idx]]
            i = name_line_idx + 2
            continue

        new_segment = [*intro_lines, "", name_line, lines[table_header_idx]]
        lines[name_line_idx : table_header_idx + 1] = new_segment
        fixes += 1
        i = name_line_idx + len(new_segment)

    if fixes > 0:
        filepath.write_text("\n".join(lines), encoding="utf-8")
    return fixes


def cmd_reorder(args):
    """reorder 子命令入口"""
    input_path = Path(args.input)
    if not input_path.exists():
        show_error(f"路径不存在: {input_path}")
        sys.exit(1)

    md_files = collect_md_files(input_path)
    total_fixes = 0
    for f in md_files:
        fixes = reorder_fix_file(f)
        if fixes > 0:
            print(f"  {f.name}: 修复 {fixes} 个表名位置")
        total_fixes += fixes

    print(f"\n共修复 {total_fixes} 个表名位置")


# ── 主入口 ────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="表格标准化工具集",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""子命令示例:
  %(prog)s check md_final/            检查表名 + 引导段落
  %(prog)s check md_final/ --fix      自动插入占位
  %(prog)s reorder md_final/          修复表名位置
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check
    p_check = subparsers.add_parser("check", help="检查表名 + 引导段落")
    p_check.add_argument("input", help="MD 文件或目录路径")
    p_check.add_argument("--fix", action="store_true", help="插入占位表名和引导标记")
    p_check.add_argument("--min-intro", type=int, default=80, help="引导段落最低字数（默认 80）")

    # reorder
    p_reorder = subparsers.add_parser("reorder", help="修复表名位置（移到表格正上方）")
    p_reorder.add_argument("input", help="MD 文件或目录路径")

    args = parser.parse_args()

    if args.command == "check":
        cmd_check(args)
    elif args.command == "reorder":
        cmd_reorder(args)


if __name__ == "__main__":
    main()
