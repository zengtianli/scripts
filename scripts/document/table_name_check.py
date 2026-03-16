#!/usr/bin/env python3
"""
表格标准化检查脚本

两个 check/fix 功能：
  1. 表名检查 — 每个表格前必须有 表X-Y 描述 行
  2. 引导段落检查 — 表格前必须有 ≥80 字引导段落（非标题行）

编号规则：
  - 章节号 = 文件名数字（01.md → 1）
  - 章内顺序：表1-1, 表1-2, ...
  - 判断已有表名：往上跳过空行，第一个非空行匹配 ^表\\d+ 则已有

兼容：md_docx_template.py L431 re.match(r'^表\\d+', stripped) → table_title 样式
"""

import sys
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_info, show_warning
from file_ops import show_version_info

SCRIPT_NAME = "table_name_check"
SCRIPT_VERSION = "1.0.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2026-03-14"

# 表名正则：表X-Y 或 表X 开头
TABLE_NAME_RE = re.compile(r'^表\d+')

# 表格分隔行正则：|---|---|
TABLE_SEP_RE = re.compile(r'^\|[\s\-:]+(\|[\s\-:]+)+\|?\s*$')


def is_in_code_block(lines: list[str], line_idx: int) -> bool:
    """判断某行是否在代码块内"""
    in_code = False
    for i in range(line_idx):
        if lines[i].strip().startswith("```"):
            in_code = not in_code
    return in_code


def extract_chapter_num(filename: str) -> int:
    """从文件名提取章节号：01.md → 1"""
    m = re.match(r'(\d+)', filename)
    if m:
        return int(m.group(1))
    return 0


def find_tables(lines: list[str]) -> list[dict]:
    """找到所有表格的位置（表头行 index）

    表格定义：| xxx | 行后紧跟 |---|---| 分隔行
    返回表头行的 index 列表
    """
    tables = []
    for i in range(len(lines) - 1):
        if is_in_code_block(lines, i):
            continue
        stripped = lines[i].strip()
        next_stripped = lines[i + 1].strip() if i + 1 < len(lines) else ""
        # 表头行：以 | 开头和结尾
        if stripped.startswith("|") and stripped.endswith("|"):
            # 下一行是分隔行
            if TABLE_SEP_RE.match(next_stripped):
                # 确认这不是表格中间行（上一行也是表格行的话就跳过）
                if i > 0:
                    prev = lines[i - 1].strip()
                    if prev.startswith("|") and prev.endswith("|"):
                        continue
                tables.append({"header_line": i})
    return tables


def check_table_name(lines: list[str], table: dict) -> dict | None:
    """检查表格是否有表名，返回 issue 或 None

    从表头行往上找，搜索范围最多 10 行，跳过空行和引导段落，
    找到匹配 ^表\\d+ 的行则认为有表名。遇到标题行(#)或另一个
    表格行(|)则停止搜索。
    """
    header_line = table["header_line"]

    # 往上搜索，最多查找 10 行
    j = header_line - 1
    search_limit = max(0, header_line - 10)
    while j >= search_limit:
        stripped = lines[j].strip()

        # 跳过空行
        if not stripped:
            j -= 1
            continue

        # 遇到标题行，停止搜索
        if stripped.startswith("#"):
            break

        # 遇到另一个表格行，停止搜索
        if stripped.startswith("|") and stripped.endswith("|"):
            break

        # 检查是否为表名
        if TABLE_NAME_RE.match(stripped):
            table["name_line"] = j
            table["has_name"] = True
            return None

        # 普通段落文字，继续向上搜索
        j -= 1

    # 没有表名
    table["has_name"] = False
    return {
        "type": "缺表名",
        "line": header_line + 1,
        "fixable": True,
    }


def check_table_intro(lines: list[str], table: dict, min_chars: int = 80) -> dict | None:
    """检查表格前是否有充分的引导段落

    引导段落可以在两个位置：
    1. 表名行与表头行之间（subagent 常用格式）
    2. 表名行之上（传统格式）
    取两处中最长的一段作为引导语。
    """
    header_line = table["header_line"]
    name_line = table.get("name_line")

    best_intro = ""

    # 位置1：表名行与表头行之间
    if name_line is not None and header_line - name_line > 2:
        for j in range(name_line + 1, header_line):
            stripped = lines[j].strip()
            if not stripped:
                continue
            if stripped.startswith("|") or stripped.startswith("#"):
                continue
            if stripped.startswith(">"):
                continue
            clean = re.sub(r'[*#>\[\]`]', '', stripped)
            if len(clean) > len(best_intro):
                best_intro = clean

    # 位置2：表名行（或表头行）之上
    start = (name_line if name_line is not None else header_line) - 1
    j = start
    while j >= 0 and lines[j].strip() == "":
        j -= 1

    if j >= 0:
        stripped = lines[j].strip()
        # 跳过 blockquote
        if stripped.startswith(">"):
            k = j - 1
            while k >= 0 and (lines[k].strip().startswith(">") or lines[k].strip() == ""):
                k -= 1
            if k >= 0:
                stripped = lines[k].strip()
            else:
                stripped = ""
        # 标题行或表格行不算引导
        if not stripped.startswith("#") and not (stripped.startswith("|") and stripped.endswith("|")):
            clean = re.sub(r'[*#>\[\]`]', '', stripped)
            if len(clean) > len(best_intro):
                best_intro = clean

    if len(best_intro) == 0:
        return {
            "type": "缺引导段落",
            "line": header_line + 1,
            "intro_len": 0,
            "fixable": True,
        }

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
    """在缺表名的表格前插入占位表名，在缺引导处插入标记

    从后往前插入，避免行号偏移
    """
    lines = text.split("\n")
    tables = find_tables(lines)

    # 先收集所有需要插入的内容（从后往前处理）
    insertions = []  # (line_idx, content_before) — 在 line_idx 之前插入

    table_counter = 0
    for table in tables:
        table_counter += 1
        name_issue = check_table_name(lines, table)
        intro_issue = check_table_intro(lines, table, min_intro_chars)

        if name_issue:
            # 需要在表头行前插入表名占位
            table_name = f"表{chapter_num}-{table_counter} [待命名]"
            insertions.append({
                "line": table["header_line"],
                "content": table_name,
                "type": "name",
            })

        if intro_issue:
            # 需要在表名行（或表头行）前插入引导标记
            insert_before = table.get("name_line", table["header_line"])
            # 如果同时要插入表名，引导标记在表名之前
            if name_issue:
                insert_before = table["header_line"]
            insertions.append({
                "line": insert_before,
                "content": "<!-- TABLE_NEEDS_INTRO -->",
                "type": "intro",
            })

    # 按行号从大到小排序，同一行先插 name 再插 intro（intro 在更前面）
    # 排序：先按 line 降序，同一行 name 在 intro 前面（name 先插入，在更靠近表头的位置）
    insertions.sort(key=lambda x: (-x["line"], x["type"] == "name"))

    for ins in insertions:
        idx = ins["line"]
        content = ins["content"]
        # 在 idx 之前插入空行 + 内容 + 空行
        lines.insert(idx, "")
        lines.insert(idx, content)
        # 如果上面不是空行，再加一个空行
        if idx > 0 and lines[idx - 1].strip() != "":
            lines.insert(idx, "")

    return "\n".join(lines)


# ── 报告输出 ──────────────────────────────────────────────────

def format_report(filepath: str, name_issues: list, intro_issues: list) -> str:
    """格式化检查报告"""
    parts = []
    parts.append(f"文件: {filepath}")
    parts.append("")

    total = 0

    # 缺表名
    if name_issues:
        parts.append(f"[缺表名] {len(name_issues)} 个表格")
        for item in name_issues:
            parts.append(f'  L{item["line"]}: 表格无表名')
        total += len(name_issues)
    else:
        parts.append("[缺表名] 无问题")
    parts.append("")

    # 缺引导段落
    if intro_issues:
        parts.append(f"[缺引导段落] {len(intro_issues)} 个表格")
        for item in intro_issues:
            if item["type"] == "缺引导段落":
                parts.append(f'  L{item["line"]}: 标题后直接跟表格')
            else:
                parts.append(
                    f'  L{item["line"]}: 引导语仅{item["intro_len"]}字'
                    f'（要求≥{item.get("min_chars", 80)}字）'
                    f' — "{item.get("intro_text", "")}"'
                )
        total += len(intro_issues)
    else:
        parts.append("[缺引导段落] 无问题")
    parts.append("")

    parts.append("─" * 40)
    parts.append(f"小计: {total} 个问题")

    return "\n".join(parts)


# ── 主流程 ────────────────────────────────────────────────────

def process_file(filepath: Path, do_fix: bool, min_intro: int) -> dict:
    """处理单个文件"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    chapter_num = extract_chapter_num(filepath.name)

    tables = find_tables(lines)
    if not tables:
        print(f"\n文件: {filepath}")
        print("  无表格，跳过\n")
        return {"total": 0, "name_missing": 0, "intro_missing": 0,
                "tables": 0, "file": str(filepath)}

    name_issues = []
    intro_issues = []

    table_counter = 0
    for table in tables:
        table_counter += 1
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


def main():
    parser = argparse.ArgumentParser(
        description="表格标准化检查（表名 + 引导段落）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s md_final/                检查模式
  %(prog)s md_final/ --fix          插入占位表名和引导标记
  %(prog)s md_final/01.md           检查单个文件
  %(prog)s md_final/ --min-intro 40 放宽引导段落要求到 40 字
""",
    )
    parser.add_argument("input", help="MD 文件或目录路径")
    parser.add_argument("--fix", action="store_true",
                        help="插入占位表名和 TABLE_NEEDS_INTRO 标记")
    parser.add_argument("--min-intro", type=int, default=80,
                        help="引导段落最低字数（默认 80）")
    parser.add_argument("--version", action="store_true",
                        help="显示版本信息")

    args = parser.parse_args()

    if args.version:
        show_version_info(SCRIPT_NAME, SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)
        return

    input_path = Path(args.input)

    if not input_path.exists():
        show_error(f"路径不存在: {input_path}")
        sys.exit(1)

    # 收集文件
    if input_path.is_dir():
        md_files = sorted(input_path.glob("*.md"))
        # 排除 merged.md
        md_files = [f for f in md_files if f.name != "merged.md"
                    and not f.name.startswith("~")]
        if not md_files:
            show_error(f"目录中没有 .md 文件: {input_path}")
            sys.exit(1)
        show_info(f"发现 {len(md_files)} 个 MD 文件")
    else:
        md_files = [input_path]

    # 逐文件处理
    all_stats = []
    for f in md_files:
        stats = process_file(f, args.fix, args.min_intro)
        all_stats.append(stats)

    # 多文件汇总
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


if __name__ == "__main__":
    main()
