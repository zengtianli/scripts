#!/usr/bin/env python3
"""frontmatter_gen.py — 批量生成 MD frontmatter

扫描指定目录下的 Markdown 文件，调用 Claude 生成
description + tags 的 YAML frontmatter 并写入文件头部。
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path

IGNORE_DIRS = {".git", "_site", "__pycache__", "node_modules", ".DS_Store"}

SYSTEM_PROMPT = (
    "你是文档分析助手。根据文档内容生成 YAML frontmatter。"
    "只返回 frontmatter 块（含 --- 分隔符），不要其他文字。"
    "description 用中文，≤50字。tags 3-5 个，用中英文均可。"
    '格式：\n---\ndescription: "描述"\ntags: [tag1, tag2, tag3]\n---'
)


def has_frontmatter(text: str) -> bool:
    """检查文本是否已有 YAML frontmatter（以 --- 开头且有第二个 ---）"""
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        return False
    # 查找第二个 ---（从第一个之后开始搜索）
    second = text.find("---", 4)
    return second != -1


def call_llm(client, content: str) -> str:
    """调用 Claude 生成 frontmatter。"""
    from tools.llm_client import chat

    return chat(
        system=SYSTEM_PROMPT,
        message=f"为以下文档生成 frontmatter：\n\n{content[:2000]}",
    )


def parse_frontmatter_response(text: str) -> str | None:
    """从 API 响应中提取 --- 之间的 frontmatter 块。

    容错处理模型返回多余文字的情况。
    返回完整的 frontmatter 块（含 --- 分隔符和尾部换行），失败返回 None。
    """
    # 尝试匹配 --- 块
    match = re.search(r"---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    inner = match.group(1).strip()
    if not inner:
        return None
    return f"---\n{inner}\n---\n"


def scan_files(src_dir: str) -> list[tuple[str, str]]:
    """递归扫描目录下的 .md 文件，跳过 IGNORE_DIRS。

    返回 [(relative_path, absolute_path), ...] 按相对路径排序。
    """
    src = Path(src_dir).resolve()
    results = []
    for root, dirs, files in os.walk(src):
        # 原地修改 dirs 以跳过忽略目录
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for f in files:
            if f.endswith(".md"):
                abs_path = os.path.join(root, f)
                rel_path = os.path.relpath(abs_path, src)
                results.append((rel_path, abs_path))
    results.sort(key=lambda x: x[0])
    return results


def process_file(filepath: str, content: str, client) -> str | None:
    """对单个文件调用 API 生成 frontmatter。

    返回 frontmatter 字符串，失败返回 None。
    """
    try:
        raw = call_llm(client, content)
    except Exception as e:
        print(f"  Error: {e}")
        return None

    fm = parse_frontmatter_response(raw)
    if fm is None:
        print(f"  Failed to parse response: {raw[:100]}")
        return None
    return fm


def main():
    parser = argparse.ArgumentParser(description="批量为 Markdown 文件生成 YAML frontmatter（智谱 API）")
    parser.add_argument("src_dir", help="要扫描的目录路径")
    parser.add_argument("--dry-run", action="store_true", help="只列出会处理的文件，不调用 API")
    parser.add_argument("--file", dest="single_file", help="只处理单个文件（相对于 src_dir 的路径）")
    args = parser.parse_args()

    src_dir = args.src_dir
    if not os.path.isdir(src_dir):
        print(f"Error: '{src_dir}' is not a directory")
        sys.exit(1)

    client = None  # kept for interface compatibility

    # 收集文件
    if args.single_file:
        abs_path = os.path.join(os.path.abspath(src_dir), args.single_file)
        if not os.path.isfile(abs_path):
            print(f"Error: file not found: {abs_path}")
            sys.exit(1)
        files = [(args.single_file, abs_path)]
    else:
        files = scan_files(src_dir)

    if not files:
        print("No .md files found.")
        return

    # 过滤已有 frontmatter 的文件
    to_process = []
    skipped = 0
    for rel, abs_path in files:
        try:
            content = Path(abs_path).read_text(encoding="utf-8")
        except Exception as e:
            print(f"Warning: cannot read {rel}: {e}")
            skipped += 1
            continue
        if has_frontmatter(content):
            skipped += 1
            continue
        to_process.append((rel, abs_path, content))

    total = len(to_process)

    # dry-run 模式
    if args.dry_run:
        print(f"Files to process ({total}):")
        for rel, _, _ in to_process:
            print(f"  {rel}")
        print(f"\nTotal: {total} files to process, {skipped} skipped (already have frontmatter)")
        return

    if total == 0:
        print(f"All files already have frontmatter. Skipped {skipped} files.")
        return

    print(f"Processing {total} files (skipping {skipped} with existing frontmatter)...\n")

    processed = 0
    failed = 0

    for i, (rel, abs_path, content) in enumerate(to_process, 1):
        print(f"[{i}/{total}] Processing: {rel}")

        fm = process_file(abs_path, content, client)
        if fm is None:
            failed += 1
            print("  FAILED")
            continue

        # 写入文件头部
        try:
            new_content = fm + "\n" + content
            Path(abs_path).write_text(new_content, encoding="utf-8")
            processed += 1
            # 显示生成的 description
            desc_match = re.search(r'description:\s*"(.+?)"', fm)
            desc = desc_match.group(1) if desc_match else "(parsed)"
            print(f"  OK: {desc}")
        except Exception as e:
            failed += 1
            print(f"  Write error: {e}")

        # Rate limiting: 0.5s 间隔
        if i < total:
            time.sleep(0.5)

    print(f"\nDone! Processed {processed} files, skipped {skipped}, failed {failed}")


if __name__ == "__main__":
    main()
