#!/usr/bin/env python3
"""
审阅规则摘要生成器 (review_summary.py)

从 review rules JSON 生成审阅摘要报告。

用法：
  python3 review_summary.py rules.json                    # 输出到 stdout
  python3 review_summary.py rules.json -o summary.md       # 输出到文件
  python3 review_summary.py rules1.json rules2.json --merge # 合并多个规则文件并去重
  python3 review_summary.py rules1.json rules2.json --merge -o merged.json  # 输出合并后 JSON

规则 JSON 格式：
  [{"find": "旧文本", "replace": "新文本", "comment": "可选说明"}]
"""

import argparse
import json


def load_rules(paths: list[str]) -> list[dict]:
    """加载一个或多个 rules JSON 文件"""
    all_rules = []
    for path in paths:
        with open(path, encoding="utf-8") as f:
            rules = json.load(f)
        all_rules.extend(rules)
    return all_rules


def deduplicate_rules(rules: list[dict]) -> list[dict]:
    """去重规则：基于 find 字段去重，保留 comment 最长的版本"""
    seen = {}
    for rule in rules:
        key = rule["find"]
        if key not in seen:
            seen[key] = rule
        else:
            # 保留 comment 更详细的版本
            existing_comment = seen[key].get("comment", "")
            new_comment = rule.get("comment", "")
            if len(new_comment) > len(existing_comment):
                seen[key] = rule
    return list(seen.values())


def _remap_dimension_tag(comment: str) -> str:
    """将旧六维标签映射到新四维标签。

    映射规则：
      原 D1 → 新 D1（不变）
      原 D2 → 新 D2（合并）
      原 D3 → 新 D2（合并）
      原 D4 → 新 D3（合并）
      原 D5 → 新 D3（合并）
      原 D6 → 新 D4
    """
    tag_map = {
        "[D3]": "[D2]",
        "[D4]": "[D3]",
        "[D5]": "[D3]",
        "[D6]": "[D4]",
    }
    for old, new in tag_map.items():
        comment = comment.replace(old, new)
    return comment


def classify_by_dimension(rules: list[dict]) -> dict[str, list[dict]]:
    """按四维分类（溯源链 / 立场与措辞 / 预判评审 / 数据纵深）"""
    dimension_map = {
        "D1": "溯源链 (Traceability)",
        "D2": "立场与措辞 (Positioning & Diplomacy)",
        "D3": "预判评审 (Anticipation)",
        "D4": "数据纵深 (Data Depth)",
    }
    classified = {k: [] for k in dimension_map}
    classified["未分类"] = []

    for rule in rules:
        comment = _remap_dimension_tag(rule.get("comment", ""))
        matched = False
        for dim_key in dimension_map:
            if dim_key in comment:
                classified[dim_key].append(rule)
                matched = True
                break
        if not matched:
            classified["未分类"].append(rule)

    # 移除空分类
    return {k: v for k, v in classified.items() if v}


def classify_by_type(rules: list[dict]) -> dict[str, list[dict]]:
    """按修改类型分类"""
    types = {
        "文字修订": [],  # find != replace, replace 非空
        "删除建议": [],  # replace 为空
        "仅批注": [],  # find == replace 或无 replace
    }
    for rule in rules:
        find = rule.get("find", "")
        replace = rule.get("replace", "")
        if not replace:
            types["删除建议"].append(rule)
        elif find == replace:
            types["仅批注"].append(rule)
        else:
            types["文字修订"].append(rule)
    return {k: v for k, v in types.items() if v}


def generate_summary(rules: list[dict]) -> str:
    """生成 Markdown 摘要报告"""
    lines = []
    lines.append("# 审阅摘要报告\n")
    lines.append(f"共 **{len(rules)}** 条审阅意见。\n")

    # 按类型统计
    by_type = classify_by_type(rules)
    lines.append("## 修改类型统计\n")
    for tname, trules in by_type.items():
        lines.append(f"- {tname}：{len(trules)} 条")
    lines.append("")

    # 按维度统计
    by_dim = classify_by_dimension(rules)
    lines.append("## 四维分类统计\n")
    for dim, drules in by_dim.items():
        lines.append(f"- {dim}：{len(drules)} 条")
    lines.append("")

    # 详细列表
    lines.append("## 详细修改列表\n")
    for i, rule in enumerate(rules, 1):
        find = rule.get("find", "")
        replace = rule.get("replace", "")
        comment = rule.get("comment", "")

        # 截断显示
        find_short = find[:50] + "..." if len(find) > 50 else find
        replace_short = replace[:50] + "..." if len(replace) > 50 else replace

        lines.append(f"### {i}. {comment.split(']')[0] + ']' if ']' in comment else '修改'}\n")
        if replace:
            lines.append(f"- **原文**：{find_short}")
            lines.append(f"- **改为**：{replace_short}")
        else:
            lines.append(f"- **删除**：{find_short}")
        if comment:
            lines.append(f"- **说明**：{comment}")
        lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="审阅规则摘要生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", help="输入 rules JSON 文件")
    parser.add_argument("-o", "--output", help="输出文件路径")
    parser.add_argument("--merge", action="store_true", help="合并多个规则文件并去重")

    args = parser.parse_args()

    rules = load_rules(args.inputs)

    if args.merge:
        original_count = len(rules)
        rules = deduplicate_rules(rules)
        dedup_count = original_count - len(rules)

        if args.output and args.output.endswith(".json"):
            # 输出合并后的 JSON
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(rules, f, ensure_ascii=False, indent=2)
            print(f"合并完成：{original_count} → {len(rules)} 条（去重 {dedup_count}）")
            print(f"已输出到 {args.output}")
            return
        else:
            print(f"合并：{original_count} → {len(rules)} 条（去重 {dedup_count}）\n")

    summary = generate_summary(rules)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(summary)
        print(f"摘要已输出到 {args.output}")
    else:
        print(summary)


if __name__ == "__main__":
    main()
