#!/usr/bin/env python3
"""
表名位置修复脚本

将表名从引导段落上方移到表格正上方（紧贴表头，无空行）。

修复前:
    表X-Y 名称
    [空行]
    引导段落
    [空行]
    | header |

修复后:
    引导段落
    [空行]
    表X-Y 名称
    | header |
"""

import sys
import re
from pathlib import Path

TABLE_NAME_RE = re.compile(r'^表\d+-\d+\s')
TABLE_SEP_RE = re.compile(r'^\|[\s\-:]+(\|[\s\-:]+)+\|?\s*$')


def is_table_header(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|")


def fix_file(filepath: Path) -> int:
    """修复单个文件，返回修复数量"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")
    fixes = 0

    # 找到所有表名行
    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        if not TABLE_NAME_RE.match(stripped):
            i += 1
            continue

        # 找到表名行，记录位置
        name_line_idx = i
        name_line = lines[i]

        # 向下找表头行（| xxx |），同时收集中间的引导段落
        j = i + 1
        intro_lines = []
        found_table = False

        while j < len(lines):
            jstripped = lines[j].strip()

            if jstripped == "":
                j += 1
                continue

            if is_table_header(jstripped):
                # 检查下一行是否为分隔行
                if j + 1 < len(lines) and TABLE_SEP_RE.match(lines[j + 1].strip()):
                    found_table = True
                    table_header_idx = j
                    break
                else:
                    # 不是表格，是普通 | 行
                    intro_lines.append(lines[j])
                    j += 1
                    continue

            if jstripped.startswith("#"):
                # 遇到标题，表名和表格不连续
                break

            # 普通文本行 = 引导段落
            intro_lines.append(lines[j])
            j += 1

        if not found_table:
            i += 1
            continue

        # 检查是否需要修复：表名行不在表头行的正上方
        # 如果表名行紧挨表头行（中间只有空行），且没有引导段落在中间，跳过
        if not intro_lines:
            # 没有引导段落，但需要确保表名紧贴表头（无空行）
            # 删除表名和表头之间的空行
            new_segment = [name_line, lines[table_header_idx]]
            # 替换从 name_line_idx 到 table_header_idx
            lines[name_line_idx:table_header_idx + 1] = [name_line, lines[table_header_idx]]
            # 不计为修复
            i = name_line_idx + 2
            continue

        # 有引导段落在表名和表头之间 → 需要重排
        # 新顺序：引导段落 → 空行 → 表名 → 表头（无空行）
        new_segment = []
        for il in intro_lines:
            new_segment.append(il)
        new_segment.append("")
        new_segment.append(name_line)
        new_segment.append(lines[table_header_idx])

        # 替换从 name_line_idx 到 table_header_idx（包含）
        lines[name_line_idx:table_header_idx + 1] = new_segment
        fixes += 1

        # 继续处理下一个
        i = name_line_idx + len(new_segment)

    if fixes > 0:
        filepath.write_text("\n".join(lines), encoding="utf-8")

    return fixes


def main():
    if len(sys.argv) < 2:
        print("用法: table_name_reorder.py <file_or_dir>")
        sys.exit(1)

    path = Path(sys.argv[1])

    if path.is_dir():
        md_files = sorted(path.glob("*.md"))
        md_files = [f for f in md_files if f.name != "merged.md"]
    else:
        md_files = [path]

    total_fixes = 0
    for f in md_files:
        fixes = fix_file(f)
        if fixes > 0:
            print(f"  {f.name}: 修复 {fixes} 个表名位置")
        total_fixes += fixes

    print(f"\n共修复 {total_fixes} 个表名位置")


if __name__ == "__main__":
    main()
