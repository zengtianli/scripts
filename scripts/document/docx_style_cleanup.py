#!/usr/bin/env python3
"""
Word 文档样式清理工具 (docx_style_cleanup.py)

功能：
  1. 重命名样式（只改显示名，不改内部 ID，安全）
  2. 合并样式（把 A 样式的段落全部改用 B 样式）
  3. 删除未使用的样式定义
  4. 生成清理报告

用法：
  python3 docx_style_cleanup.py input.docx -o output.docx --config rules.json
  python3 docx_style_cleanup.py input.docx --preview   # 只看会改什么，不实际改
"""

import argparse
import json
import sys
import zipfile
from io import BytesIO

from lxml import etree

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def load_docx(path: str):
    """加载 docx，返回 (zip_bytes_dict, styles_tree, doc_tree)"""
    files = {}
    with zipfile.ZipFile(path, "r") as zf:
        for info in zf.infolist():
            files[info.filename] = zf.read(info.filename)

    styles_tree = etree.fromstring(files["word/styles.xml"])
    doc_tree = etree.fromstring(files["word/document.xml"])
    return files, styles_tree, doc_tree


def save_docx(files: dict, styles_tree, doc_tree, output_path: str):
    """保存修改后的 docx"""
    files["word/styles.xml"] = etree.tostring(styles_tree, xml_declaration=True, encoding="UTF-8", standalone=True)
    files["word/document.xml"] = etree.tostring(doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True)

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    with open(output_path, "wb") as f:
        f.write(buf.getvalue())


def get_style_map(styles_tree) -> dict:
    """从 styles.xml 提取 styleId → {name, type, basedOn}"""
    result = {}
    for s in styles_tree.findall(f".//{{{W}}}style"):
        sid = s.get(f"{{{W}}}styleId", "")
        stype = s.get(f"{{{W}}}type", "")
        ne = s.find(f"{{{W}}}name")
        name = ne.get(f"{{{W}}}val", sid) if ne is not None else sid
        based = s.find(f"{{{W}}}basedOn")
        base_id = based.get(f"{{{W}}}val", "") if based is not None else ""
        result[sid] = {"name": name, "type": stype, "basedOn": base_id, "elem": s}
    return result


def get_used_style_ids(doc_tree) -> set:
    """扫描 document.xml，找出所有被使用的样式 ID"""
    used = set()
    # 段落样式
    for ps in doc_tree.iter(f"{{{W}}}pStyle"):
        used.add(ps.get(f"{{{W}}}val", ""))
    # 字符样式
    for rs in doc_tree.iter(f"{{{W}}}rStyle"):
        used.add(rs.get(f"{{{W}}}val", ""))
    # 表格样式
    for ts in doc_tree.iter(f"{{{W}}}tblStyle"):
        used.add(ts.get(f"{{{W}}}val", ""))
    used.discard("")
    return used


def get_basedOn_ids(style_map: dict, used_ids: set) -> set:
    """递归找出所有被使用样式依赖的 basedOn 样式"""
    needed = set(used_ids)
    queue = list(used_ids)
    while queue:
        sid = queue.pop()
        info = style_map.get(sid)
        if info and info["basedOn"] and info["basedOn"] not in needed:
            needed.add(info["basedOn"])
            queue.append(info["basedOn"])
    return needed


# Word 内置样式 ID，不能删
BUILTIN_KEEP = {
    "a",  # Normal
    "a0",  # Default Paragraph Font
}


def cleanup(
    files: dict,
    styles_tree,
    doc_tree,
    renames: dict = None,
    merges: dict = None,
    delete_unused: bool = True,
    preview: bool = False,
) -> list[str]:
    """
    执行样式清理。

    Args:
        renames: {old_display_name: new_display_name} 重命名映射
        merges: {from_style_id: to_style_id} 合并映射
        delete_unused: 是否删除未使用的样式
        preview: 只生成报告不修改

    Returns:
        操作日志列表
    """
    log = []
    style_map = get_style_map(styles_tree)

    # ── 1. 合并样式 ──
    if merges:
        for from_id, to_id in merges.items():
            if from_id not in style_map:
                log.append(f"⚠️  合并跳过：源样式 ID '{from_id}' 不存在")
                continue
            if to_id not in style_map:
                log.append(f"⚠️  合并跳过：目标样式 ID '{to_id}' 不存在")
                continue

            count = 0
            if not preview:
                for ps in doc_tree.iter(f"{{{W}}}pStyle"):
                    if ps.get(f"{{{W}}}val") == from_id:
                        ps.set(f"{{{W}}}val", to_id)
                        count += 1
            else:
                for ps in doc_tree.iter(f"{{{W}}}pStyle"):
                    if ps.get(f"{{{W}}}val") == from_id:
                        count += 1

            from_name = style_map[from_id]["name"]
            to_name = style_map[to_id]["name"]
            log.append(f"🔀 合并：{from_name} ({from_id}) → {to_name} ({to_id})，{count} 个段落")

    # ── 2. 重命名样式 ──
    if renames:
        # 建立 name → styleId 映射
        name_to_id = {}
        for sid, info in style_map.items():
            name_to_id[info["name"]] = sid

        for old_name, new_name in renames.items():
            sid = name_to_id.get(old_name)
            if not sid:
                log.append(f"⚠️  重命名跳过：找不到样式 '{old_name}'")
                continue
            if not preview:
                ne = style_map[sid]["elem"].find(f"{{{W}}}name")
                if ne is not None:
                    ne.set(f"{{{W}}}val", new_name)
            log.append(f"✏️  重命名：{old_name} → {new_name}")

    # ── 3. 删除未使用样式 ──
    if delete_unused:
        # 重新扫描（合并后使用情况可能变了）
        used_ids = get_used_style_ids(doc_tree)
        needed_ids = get_basedOn_ids(style_map, used_ids)
        needed_ids |= BUILTIN_KEEP

        # 内置 heading/toc 样式保留（即使没用到，删了可能有问题）
        for sid in style_map:
            if sid.startswith("TOC") or sid in ("a", "a0"):
                needed_ids.add(sid)

        to_delete = []
        for sid, info in style_map.items():
            if sid not in needed_ids:
                to_delete.append((sid, info["name"]))

        if to_delete:
            log.append(f"\n🗑️  删除 {len(to_delete)} 个未使用样式：")
            for sid, name in sorted(to_delete, key=lambda x: x[1]):
                log.append(f"   - {name} ({sid})")
                if not preview:
                    for s in styles_tree.findall(f".//{{{W}}}style"):
                        if s.get(f"{{{W}}}styleId") == sid:
                            s.getparent().remove(s)
                            break

    return log


def main():
    parser = argparse.ArgumentParser(description="Word 文档样式清理工具")
    parser.add_argument("input", help="输入 .docx 文件")
    parser.add_argument("-o", "--output", help="输出 .docx 文件")
    parser.add_argument("--config", help="清理规则 JSON 文件")
    parser.add_argument("--preview", action="store_true", help="只预览，不实际修改")
    args = parser.parse_args()

    if not args.output and not args.preview:
        print("请指定 -o 输出文件或使用 --preview 预览模式")
        sys.exit(1)

    # 加载配置
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {}

    files, styles_tree, doc_tree = load_docx(args.input)

    log = cleanup(
        files,
        styles_tree,
        doc_tree,
        renames=config.get("renames"),
        merges=config.get("merges"),
        delete_unused=config.get("delete_unused", True),
        preview=args.preview,
    )

    for line in log:
        print(line)

    if not args.preview and args.output:
        save_docx(files, styles_tree, doc_tree, args.output)
        print(f"\n📄 已保存到 {args.output}")
    elif args.preview:
        print("\n（预览模式，未修改文件）")


if __name__ == "__main__":
    main()
