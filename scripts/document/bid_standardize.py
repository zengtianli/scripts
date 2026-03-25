#!/usr/bin/env python3
"""
标书 MD 结构标准化脚本

六个 check/fix 功能：
  1. 标题级别校正 — 章标题必须 #，子标题 ## ### 顺延
  2. 评分引用注入 — 章标题后必须有 blockquote，内容来自 scoring.json
  3. 编号标签清理 — 去掉"创新点一：""难点二："等前缀
  4. 加粗标题提升 — 独占一行的 **XXX** 提升为对应层级的 ### 标题
  5. 标题编号补全 — ### 标题自动按 X.Y.Z 格式编号
  6. 数据来源提取 — 行内 [数据来源：XX] 和 <!-- SOURCE: XX --> 提取为 blockquote
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_error, show_info, show_success
from file_ops import show_version_info
import contextlib

SCRIPT_NAME = "bid_standardize"
SCRIPT_VERSION = "1.3.0"
SCRIPT_AUTHOR = "tianli"
SCRIPT_UPDATED = "2026-03-14"

# ── 编号标签正则 ──────────────────────────────────────────────

NUMBERED_LABEL_RE = re.compile(
    r"(创新点|难点|亮点|特点|重点|要点|优势|挑战)"
    r"[一二三四五六七八九十\d]+"
    r"[：:]"
)

# ── 加粗标题正则 ─────────────────────────────────────────────

BOLD_HEADING_RE = re.compile(r"^\*\*(.+)\*\*$")

# ── 标题编号正则 ─────────────────────────────────────────────

# 匹配 ## X.Y 格式的二级标题
H2_NUMBER_RE = re.compile(r"^##\s+(\d+\.\d+)\s")

# 匹配 ### X.Y.Z 格式的三级标题（已有编号）
H3_NUMBER_RE = re.compile(r"^###\s+(\d+\.\d+\.\d+)\s")

# 匹配 ### 开头但没有 X.Y.Z 编号的三级标题
H3_NO_NUMBER_RE = re.compile(r"^###\s+(?!\d+\.\d+\.\d+\s)(.+)$")

# ── 数据来源标注正则 ─────────────────────────────────────────

# 行内中括号标注：[数据来源：XX] 或 [待核实：XX]
INLINE_SOURCE_RE = re.compile(r"\[数据来源[：:](.*?)\]")
INLINE_VERIFY_RE = re.compile(r"\[待核实[：:](.*?)\]")

# HTML 注释标注：<!-- SOURCE: XX -->
HTML_SOURCE_RE = re.compile(r"\s*<!--\s*SOURCE:\s*(.*?)\s*-->")


# ── 工具函数 ──────────────────────────────────────────────────


def is_in_code_block(lines: list[str], line_idx: int) -> bool:
    """判断某行是否在代码块内"""
    in_code = False
    for i in range(line_idx):
        if lines[i].strip().startswith("```"):
            in_code = not in_code
    return in_code


def load_scoring(scoring_path: Path) -> dict:
    """加载 scoring.json，返回 {chapter_num: config}"""
    with open(scoring_path, encoding="utf-8") as f:
        data = json.load(f)
    result = {}
    for ch in data.get("chapters", []):
        result[ch["chapter"]] = ch
    return result


def match_chapter(filename: str, scoring: dict) -> dict | None:
    """通过文件名匹配 scoring 配置"""
    for _ch_num, config in scoring.items():
        pattern = config.get("file_pattern", "")
        if pattern and pattern in filename:
            return config
    return None


def build_scoring_blockquote(config: dict) -> str:
    """根据 scoring 配置生成 blockquote 文本"""
    parts = [f"> **评分标准（{config['score']}分）**：{config['scoring_text']}"]
    if config.get("bid_ref"):
        parts.append(f"> {config['bid_ref']}")
    return "\n".join(parts)


# ── 检查函数 ──────────────────────────────────────────────────


def check_heading_levels(lines: list[str]) -> list[dict]:
    """检查标题级别：章标题（含"第X章"）必须是 #"""
    issues = []
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        # 匹配 ## 第X章 或 ## 第一章 等
        m = re.match(r"^(#{2,})\s+第[一二三四五六七八九十\d]+章", stripped)
        if m:
            current_level = len(m.group(1))
            issues.append(
                {
                    "type": "标题级别",
                    "line": i + 1,
                    "current_level": current_level,
                    "content": stripped[:60],
                    "fixable": True,
                }
            )
    return issues


def check_scoring_blockquote(lines: list[str], scoring_config: dict | None) -> list[dict]:
    """检查章标题后是否有评分引用 blockquote"""
    issues = []
    if scoring_config is None:
        return issues

    expected = build_scoring_blockquote(scoring_config)

    # 找到第一个 # 标题（章标题）
    chapter_line = -1
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        if re.match(r"^#{1,2}\s+", stripped):
            chapter_line = i
            break

    if chapter_line == -1:
        return issues

    # 检查章标题之后（跳过空行）是否有 > **评分 开头的 blockquote
    has_blockquote = False
    blockquote_matches = False
    blockquote_start = -1
    blockquote_end = -1

    j = chapter_line + 1
    # 跳过空行
    while j < len(lines) and lines[j].strip() == "":
        j += 1

    if j < len(lines) and lines[j].strip().startswith("> **评分"):
        has_blockquote = True
        blockquote_start = j
        # 找到 blockquote 结束位置
        blockquote_end = j
        while blockquote_end + 1 < len(lines) and lines[blockquote_end + 1].strip().startswith(">"):
            blockquote_end += 1
        # 检查内容是否匹配
        existing = "\n".join(lines[blockquote_start : blockquote_end + 1])
        if existing.strip() == expected.strip():
            blockquote_matches = True

    if not has_blockquote:
        issues.append(
            {
                "type": "评分引用",
                "line": chapter_line + 1,
                "status": "缺失",
                "expected": expected,
                "fixable": True,
            }
        )
    elif not blockquote_matches:
        issues.append(
            {
                "type": "评分引用",
                "line": blockquote_start + 1,
                "status": "内容不匹配",
                "expected": expected,
                "blockquote_start": blockquote_start,
                "blockquote_end": blockquote_end,
                "fixable": True,
            }
        )

    return issues


def check_numbered_labels(lines: list[str]) -> list[dict]:
    """检查标题和加粗行中的编号标签前缀"""
    issues = []
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        # 仅检查标题行和加粗行
        is_heading = stripped.startswith("#")
        is_bold = stripped.startswith("**")
        if not (is_heading or is_bold):
            continue
        m = NUMBERED_LABEL_RE.search(stripped)
        if m:
            issues.append(
                {
                    "type": "编号标签",
                    "line": i + 1,
                    "label": m.group(0),
                    "content": stripped[:60],
                    "fixable": True,
                }
            )
    return issues


def check_bold_headings(lines: list[str]) -> list[dict]:
    """检查独占一行的 **加粗文本** 是否应提升为标题"""
    issues = []
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        # 跳过表格行
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        m = BOLD_HEADING_RE.match(stripped)
        if m:
            # 向上找最近的标题，确定应提升到的层级
            parent_level = 1  # 默认：如果没找到父标题，按 # 的下一级
            for j in range(i - 1, -1, -1):
                if is_in_code_block(lines, j):
                    continue
                pline = lines[j].strip()
                pm = re.match(r"^(#{1,6})\s", pline)
                if pm:
                    parent_level = len(pm.group(1))
                    break
            target_level = parent_level + 1
            issues.append(
                {
                    "type": "加粗标题",
                    "line": i + 1,
                    "content": m.group(1),
                    "parent_level": parent_level,
                    "target_level": target_level,
                    "fixable": True,
                }
            )
    return issues


def check_heading_numbers(lines: list[str]) -> list[dict]:
    """检查 ### 三级标题是否缺少 X.Y.Z 编号"""
    issues = []
    current_h2_num = None  # 当前所在的 ## 节号，如 "9.1"

    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()

        # 跟踪 ## 节号
        m2 = H2_NUMBER_RE.match(stripped)
        if m2:
            current_h2_num = m2.group(1)
            continue

        # 检查 ### 标题
        if not stripped.startswith("### "):
            continue

        # 已有 X.Y.Z 编号的跳过
        if H3_NUMBER_RE.match(stripped):
            continue

        # 没有编号的 ###
        m3 = H3_NO_NUMBER_RE.match(stripped)
        if m3 and current_h2_num:
            issues.append(
                {
                    "type": "标题编号",
                    "line": i + 1,
                    "content": m3.group(1).strip(),
                    "parent_num": current_h2_num,
                    "fixable": True,
                }
            )

    return issues


def check_source_annotations(lines: list[str]) -> list[dict]:
    """检查行内数据来源标注和 HTML SOURCE 注释"""
    issues = []
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        # 跳过表格行（表头中可能有"数据来源"列名）
        stripped = line.strip()
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        # 跳过已经是 blockquote 的行
        if stripped.startswith(">"):
            continue

        found_inline = INLINE_SOURCE_RE.findall(line)
        found_verify = INLINE_VERIFY_RE.findall(line)
        found_html = HTML_SOURCE_RE.findall(line)

        if found_inline or found_verify or found_html:
            issues.append(
                {
                    "type": "数据来源标注",
                    "line": i + 1,
                    "inline_sources": found_inline,
                    "verify_notes": found_verify,
                    "html_sources": found_html,
                    "fixable": True,
                }
            )
    return issues


# ── 修复函数 ──────────────────────────────────────────────────


def fix_heading_levels(text: str) -> str:
    """修复标题级别：将 ## 第X章 降级为 # 第X章，其余标题对应降一级"""
    lines = text.split("\n")

    # 第一遍：检测是否存在问题（## 第X章 的情况）
    has_issue = False
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        if re.match(r"^##\s+第[一二三四五六七八九十\d]+章", stripped):
            has_issue = True
            break

    if not has_issue:
        return text

    # 第二遍：所有标题降一级（## → #, ### → ##, etc.）
    result = []
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            result.append(line)
            continue
        m = re.match(r"^(#{2,})(\s+.*)$", line)
        if m:
            new_hashes = "#" * (len(m.group(1)) - 1)
            result.append(f"{new_hashes}{m.group(2)}")
        else:
            result.append(line)

    return "\n".join(result)


def fix_scoring_blockquote(text: str, scoring_config: dict | None) -> str:
    """注入或更新评分引用 blockquote"""
    if scoring_config is None:
        return text

    lines = text.split("\n")
    expected = build_scoring_blockquote(scoring_config)

    # 找到章标题
    chapter_line = -1
    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            continue
        stripped = line.strip()
        if re.match(r"^#{1,2}\s+", stripped):
            chapter_line = i
            break

    if chapter_line == -1:
        return text

    # 检查章标题之后是否有 blockquote
    j = chapter_line + 1
    while j < len(lines) and lines[j].strip() == "":
        j += 1

    if j < len(lines) and lines[j].strip().startswith("> **评分"):
        # 已有 blockquote，找到结束位置并替换
        blockquote_start = j
        blockquote_end = j
        while blockquote_end + 1 < len(lines) and lines[blockquote_end + 1].strip().startswith(">"):
            blockquote_end += 1
        lines[blockquote_start : blockquote_end + 1] = expected.split("\n")
    else:
        # 没有 blockquote，在章标题后插入
        insert_pos = chapter_line + 1
        lines.insert(insert_pos, "")
        lines.insert(insert_pos + 1, expected)
        lines.insert(insert_pos + 2, "")

    return "\n".join(lines)


def fix_numbered_labels(text: str) -> str:
    """去掉标题和加粗行中的编号标签前缀"""
    lines = text.split("\n")
    result = []

    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            result.append(line)
            continue
        stripped = line.strip()
        is_heading = stripped.startswith("#")
        is_bold = stripped.startswith("**")
        if is_heading or is_bold:
            line = NUMBERED_LABEL_RE.sub("", line)
            # 清理可能残留的多余空格
            line = re.sub(r"  +", " ", line)
        result.append(line)

    return "\n".join(result)


def fix_bold_headings(text: str) -> str:
    """将独占一行的 **加粗文本** 提升为对应层级的标题"""
    lines = text.split("\n")
    result = []

    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            result.append(line)
            continue
        stripped = line.strip()
        # 跳过表格行
        if stripped.startswith("|") and stripped.endswith("|"):
            result.append(line)
            continue
        m = BOLD_HEADING_RE.match(stripped)
        if m:
            # 向上找最近的标题
            parent_level = 1
            for j in range(i - 1, -1, -1):
                if is_in_code_block(lines, j):
                    continue
                pline = lines[j].strip()
                pm = re.match(r"^(#{1,6})\s", pline)
                if pm:
                    parent_level = len(pm.group(1))
                    break
            target_level = parent_level + 1
            hashes = "#" * target_level
            result.append(f"{hashes} {m.group(1)}")
        else:
            result.append(line)

    return "\n".join(result)


def fix_heading_numbers(text: str) -> str:
    """为无编号的 ### 三级标题自动添加 X.Y.Z 编号"""
    lines = text.split("\n")
    result = []
    current_h2_num = None  # 如 "9.1"
    h3_counter = 0  # 当前 ## 下的 ### 计数器

    for i, line in enumerate(lines):
        if is_in_code_block(lines, i):
            result.append(line)
            continue
        stripped = line.strip()

        # 跟踪 ## 节号，重置 ### 计数器
        m2 = H2_NUMBER_RE.match(stripped)
        if m2:
            current_h2_num = m2.group(1)
            h3_counter = 0
            result.append(line)
            continue

        # 处理 ### 标题
        if stripped.startswith("### "):
            # 已有 X.Y.Z 编号：更新计数器但不修改
            m3 = H3_NUMBER_RE.match(stripped)
            if m3:
                # 从已有编号提取子序号以保持连续
                existing_num = m3.group(1)
                parts = existing_num.split(".")
                if len(parts) == 3:
                    with contextlib.suppress(ValueError):
                        h3_counter = int(parts[2])
                result.append(line)
                continue

            # 无编号：添加编号
            m_no = H3_NO_NUMBER_RE.match(stripped)
            if m_no and current_h2_num:
                h3_counter += 1
                title_text = m_no.group(1).strip()
                result.append(f"### {current_h2_num}.{h3_counter} {title_text}")
                continue

        result.append(line)

    return "\n".join(result)


def fix_source_annotations(text: str) -> str:
    """将行内数据来源标注和 HTML SOURCE 注释提取为下一行 blockquote"""
    lines = text.split("\n")
    result = []

    i = 0
    in_code = False
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # 跟踪代码块
        if stripped.startswith("```"):
            in_code = not in_code
            result.append(line)
            i += 1
            continue

        if in_code:
            result.append(line)
            i += 1
            continue

        # 跳过表格行和已有 blockquote
        if (stripped.startswith("|") and stripped.endswith("|")) or stripped.startswith(">"):
            result.append(line)
            i += 1
            continue

        # 收集本行的所有来源标注
        blockquotes = []

        # 提取 [数据来源：XX]
        for m in INLINE_SOURCE_RE.finditer(line):
            source_text = m.group(1).strip()
            blockquotes.append(f"> [数据来源：{source_text}]")
        line = INLINE_SOURCE_RE.sub("", line)

        # 提取 [待核实：XX]
        for m in INLINE_VERIFY_RE.finditer(line):
            note_text = m.group(1).strip()
            blockquotes.append(f"> [待核实：{note_text}]")
        line = INLINE_VERIFY_RE.sub("", line)

        # 提取 <!-- SOURCE: XX -->
        for m in HTML_SOURCE_RE.finditer(line):
            source_text = m.group(1).strip()
            if source_text == "PLACEHOLDER":
                blockquotes.append("> [待补充数据来源]")
            else:
                blockquotes.append(f"> [数据来源：{source_text}]")
        line = HTML_SOURCE_RE.sub("", line)

        # 清理行尾多余空格
        line = line.rstrip()

        result.append(line)

        # 在当前行后插入 blockquote（去重）
        if blockquotes:
            seen = set()
            unique_bqs = []
            for bq in blockquotes:
                if bq not in seen:
                    seen.add(bq)
                    unique_bqs.append(bq)
            result.append("")
            for bq in unique_bqs:
                result.append(bq)

        i += 1

    return "\n".join(result)


# ── 报告输出 ──────────────────────────────────────────────────


def format_report(
    filepath: str,
    heading_issues: list,
    scoring_issues: list,
    label_issues: list,
    bold_issues: list = None,
    number_issues: list = None,
    source_issues: list = None,
) -> str:
    """格式化检查报告"""
    if bold_issues is None:
        bold_issues = []
    if number_issues is None:
        number_issues = []
    if source_issues is None:
        source_issues = []
    parts = []
    parts.append(f"文件: {filepath}")
    parts.append("")

    total = 0
    fixable = 0

    # 标题级别
    if heading_issues:
        parts.append(f"[标题级别] 发现 {len(heading_issues)} 处")
        for item in heading_issues:
            parts.append(f"  L{item['line']}: 当前 {'#' * item['current_level']}（应为 #） — {item['content']}")
        total += len(heading_issues)
        fixable += sum(1 for i in heading_issues if i["fixable"])
    else:
        parts.append("[标题级别] 无问题")
    parts.append("")

    # 评分引用
    if scoring_issues:
        parts.append(f"[评分引用] 发现 {len(scoring_issues)} 处")
        for item in scoring_issues:
            parts.append(f"  L{item['line']}: {item['status']}")
        total += len(scoring_issues)
        fixable += sum(1 for i in scoring_issues if i["fixable"])
    else:
        parts.append("[评分引用] 无问题")
    parts.append("")

    # 编号标签
    if label_issues:
        parts.append(f"[编号标签] 发现 {len(label_issues)} 处")
        for item in label_issues:
            parts.append(f'  L{item["line"]}: "{item["label"]}" — {item["content"]}')
        total += len(label_issues)
        fixable += sum(1 for i in label_issues if i["fixable"])
    else:
        parts.append("[编号标签] 无问题")
    parts.append("")

    # 加粗标题
    if bold_issues:
        parts.append(f"[加粗标题] 发现 {len(bold_issues)} 处")
        for item in bold_issues:
            parts.append(f"  L{item['line']}: **{item['content']}** → {'#' * item['target_level']} {item['content']}")
        total += len(bold_issues)
        fixable += sum(1 for i in bold_issues if i["fixable"])
    else:
        parts.append("[加粗标题] 无问题")
    parts.append("")

    # 标题编号
    if number_issues:
        parts.append(f"[标题编号] 发现 {len(number_issues)} 处无编号")
        for item in number_issues:
            parts.append(f"  L{item['line']}: ### {item['content']} → 应编号为 {item['parent_num']}.N")
        total += len(number_issues)
        fixable += sum(1 for i in number_issues if i["fixable"])
    else:
        parts.append("[标题编号] 无问题")
    parts.append("")

    # 数据来源标注
    if source_issues:
        n_inline = sum(len(s["inline_sources"]) for s in source_issues)
        n_verify = sum(len(s["verify_notes"]) for s in source_issues)
        n_html = sum(len(s["html_sources"]) for s in source_issues)
        parts.append(
            f"[数据来源标注] {len(source_issues)} 行需提取（行内{n_inline} + 待核实{n_verify} + HTML注释{n_html}）"
        )
        total += len(source_issues)
        fixable += sum(1 for i in source_issues if i["fixable"])
    else:
        parts.append("[数据来源标注] 无问题")
    parts.append("")

    # 汇总
    parts.append("─" * 40)
    parts.append(f"小计: {total} 个问题（可修复 {fixable} 个）")

    return "\n".join(parts)


# ── 主流程 ────────────────────────────────────────────────────


def process_file(filepath: Path, scoring: dict, do_fix: bool, output_dir: Path | None) -> dict:
    """处理单个文件"""
    text = filepath.read_text(encoding="utf-8")
    lines = text.split("\n")

    # 匹配 scoring 配置
    scoring_config = match_chapter(filepath.name, scoring)

    # 检查
    heading_issues = check_heading_levels(lines)
    scoring_issues = check_scoring_blockquote(lines, scoring_config)
    label_issues = check_numbered_labels(lines)
    bold_issues = check_bold_headings(lines)
    number_issues = check_heading_numbers(lines)
    source_issues = check_source_annotations(lines)

    # 输出报告
    report = format_report(
        str(filepath), heading_issues, scoring_issues, label_issues, bold_issues, number_issues, source_issues
    )
    print(f"\n{'─' * 3} 结构标准化检查 {'─' * 3}\n")
    print(report)

    total = (
        len(heading_issues)
        + len(scoring_issues)
        + len(label_issues)
        + len(bold_issues)
        + len(number_issues)
        + len(source_issues)
    )
    fixable = (
        sum(1 for i in heading_issues if i["fixable"])
        + sum(1 for i in scoring_issues if i["fixable"])
        + sum(1 for i in label_issues if i["fixable"])
        + sum(1 for i in bold_issues if i["fixable"])
        + sum(1 for i in number_issues if i["fixable"])
        + sum(1 for i in source_issues if i["fixable"])
    )

    # 修复
    if do_fix and fixable > 0:
        fixed_text = fix_heading_levels(text)
        fixed_text = fix_scoring_blockquote(fixed_text, scoring_config)
        fixed_text = fix_numbered_labels(fixed_text)
        fixed_text = fix_bold_headings(fixed_text)
        fixed_text = fix_heading_numbers(fixed_text)
        fixed_text = fix_source_annotations(fixed_text)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / filepath.name
        else:
            out_path = filepath

        out_path.write_text(fixed_text, encoding="utf-8")
        show_success(f"已修复并保存: {out_path}")

    return {"total": total, "fixable": fixable, "file": str(filepath)}


def main():
    parser = argparse.ArgumentParser(
        description="标书 MD 结构标准化（标题级别 + 评分引用 + 编号标签）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s md_fixed/ --scoring scoring.json           检查模式
  %(prog)s md_fixed/ --scoring scoring.json --fix     修复（覆盖原文件）
  %(prog)s md_fixed/ --scoring scoring.json --fix --output-dir md_std/
""",
    )
    parser.add_argument("input", help="MD 文件或目录路径")
    parser.add_argument("--scoring", required=True, help="scoring.json 评分标准配置文件")
    parser.add_argument("--fix", action="store_true", help="自动修复")
    parser.add_argument("--output-dir", help="修复后文件的输出目录（默认覆盖原文件）")
    parser.add_argument("--version", action="store_true", help="显示版本信息")

    args = parser.parse_args()

    if args.version:
        show_version_info(SCRIPT_NAME, SCRIPT_VERSION, SCRIPT_AUTHOR, SCRIPT_UPDATED)
        return

    input_path = Path(args.input)
    scoring_path = Path(args.scoring)

    if not input_path.exists():
        show_error(f"路径不存在: {input_path}")
        sys.exit(1)

    if not scoring_path.exists():
        show_error(f"评分标准文件不存在: {scoring_path}")
        sys.exit(1)

    scoring = load_scoring(scoring_path)
    show_info(f"加载评分标准: {len(scoring)} 个章节配置")

    # 收集文件
    if input_path.is_dir():
        md_files = sorted(input_path.glob("*.md"))
        if not md_files:
            show_error(f"目录中没有 .md 文件: {input_path}")
            sys.exit(1)
        show_info(f"发现 {len(md_files)} 个 MD 文件")
    else:
        md_files = [input_path]

    output_dir = Path(args.output_dir) if args.output_dir else None

    # 逐文件处理
    all_stats = []
    for f in md_files:
        stats = process_file(f, scoring, args.fix, output_dir)
        all_stats.append(stats)

    # 多文件汇总
    if len(all_stats) > 1:
        grand_total = sum(s["total"] for s in all_stats)
        grand_fixable = sum(s["fixable"] for s in all_stats)
        print(f"\n{'═' * 3} 全部文件汇总 {'═' * 3}")
        print(f"文件数: {len(all_stats)}")
        print(f"总问题: {grand_total}")
        print(f"  可自动修复: {grand_fixable}")
        print(f"  需人工处理: {grand_total - grand_fixable}")
        print("═" * 40)

    # 退出码
    total = sum(s["total"] for s in all_stats)
    if total > 0 and not args.fix:
        sys.exit(1)


if __name__ == "__main__":
    main()
