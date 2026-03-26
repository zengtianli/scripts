#!/usr/bin/env python3
"""
Word 审阅修订工具 (docx_track_changes.py)

功能：
  read   — 读取 .docx 中的修订标记和批注
  review — 对 .docx 执行替换并写入修订标记（del/ins）和批注

用法：
  python3 docx_track_changes.py read input.docx [--format md|json]
  python3 docx_track_changes.py review input.docx -o output.docx --rules rules.json [--author "CC审阅"]

rules.json 格式：
  [{"find": "旧文本", "replace": "新文本", "comment": "可选批注"}]
"""

import argparse
import copy
import json
import os
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from docx_xml import R_NS, REL_COMMENTS, W, qn
from lxml import etree

# ═══════════════════════════════════════════════════════════════════
#  功能1: 读取修订
# ═══════════════════════════════════════════════════════════════════


def read_track_changes(docx_path: str, fmt: str = "md") -> str:
    """读取 .docx 中的修订和批注，返回 Markdown 或 JSON"""
    changes = []
    comments = []

    with zipfile.ZipFile(docx_path, "r") as zf:
        doc_xml = zf.read("word/document.xml")
        tree = etree.fromstring(doc_xml)

        for ins in tree.iter(qn("w:ins")):
            author = ins.get(qn("w:author"), "未知")
            date = ins.get(qn("w:date"), "")
            text = _extract_text(ins)
            if text.strip():
                changes.append({"type": "insert", "author": author, "date": date, "text": text})

        for dl in tree.iter(qn("w:del")):
            author = dl.get(qn("w:author"), "未知")
            date = dl.get(qn("w:date"), "")
            text = _extract_del_text(dl)
            if text.strip():
                changes.append({"type": "delete", "author": author, "date": date, "text": text})

        if "word/comments.xml" in zf.namelist():
            comments_xml = zf.read("word/comments.xml")
            ctree = etree.fromstring(comments_xml)
            for comment in ctree.iter(qn("w:comment")):
                comments.append(
                    {
                        "id": comment.get(qn("w:id"), ""),
                        "author": comment.get(qn("w:author"), "未知"),
                        "date": comment.get(qn("w:date"), ""),
                        "text": _extract_text(comment),
                    }
                )

    if fmt == "json":
        return json.dumps({"changes": changes, "comments": comments}, ensure_ascii=False, indent=2)

    # Markdown 格式
    lines = []
    if changes:
        lines.append("## 修订记录\n")
        for i, c in enumerate(changes, 1):
            icon = "插入" if c["type"] == "insert" else "删除"
            date_str = c["date"][:10] if c["date"] else ""
            lines.append(f"{i}. **{icon}** | {c['author']} | {date_str}")
            lines.append(f"   > {c['text']}\n")
    else:
        lines.append("## 修订记录\n\n无修订。\n")

    if comments:
        lines.append("## 批注\n")
        for c in comments:
            date_str = c["date"][:10] if c["date"] else ""
            lines.append(f"- **[{c['id']}]** {c['author']} ({date_str}):")
            lines.append(f"  > {c['text']}\n")

    return "\n".join(lines)


def _extract_text(node) -> str:
    """从 XML 节点中提取所有 <w:t> 文本"""
    return "".join(t.text for t in node.iter(qn("w:t")) if t.text)


def _extract_del_text(node) -> str:
    """从删除标记中提取 <w:delText> 文本"""
    parts = [t.text for t in node.iter(qn("w:delText")) if t.text]
    if not parts:
        parts = [t.text for t in node.iter(qn("w:t")) if t.text]
    return "".join(parts)


# ═══════════════════════════════════════════════════════════════════
#  功能2: 写入修订（review 命令）
# ═══════════════════════════════════════════════════════════════════


class DocxReviewer:
    """对 .docx 文件应用替换规则，生成带修订标记的新文件。保持原文格式不变。"""

    def __init__(self, docx_path: str, author: str = "CC审阅"):
        self.docx_path = docx_path
        self.author = author
        self.date = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.comment_id_counter = 0
        self.comments = []
        self.revision_id_counter = 100

        self.tmpdir = tempfile.mkdtemp(prefix="docx_review_")
        with zipfile.ZipFile(docx_path, "r") as zf:
            zf.extractall(self.tmpdir)

        doc_path = os.path.join(self.tmpdir, "word", "document.xml")
        self.doc_tree = etree.parse(doc_path)
        self.doc_root = self.doc_tree.getroot()
        self._init_comment_ids()

    def _init_comment_ids(self):
        comments_path = os.path.join(self.tmpdir, "word", "comments.xml")
        if os.path.exists(comments_path):
            ctree = etree.parse(comments_path)
            for c in ctree.getroot().iter(qn("w:comment")):
                cid = int(c.get(qn("w:id"), "0"))
                if cid >= self.comment_id_counter:
                    self.comment_id_counter = cid + 1

    def _next_rid(self) -> str:
        self.revision_id_counter += 1
        return str(self.revision_id_counter)

    def _next_comment_id(self) -> int:
        cid = self.comment_id_counter
        self.comment_id_counter += 1
        return cid

    def apply_rules(self, rules: list[dict]) -> int:
        """应用替换规则列表。返回成功替换的数量。"""
        count = 0
        for rule in rules:
            n = self._apply_one_rule(rule["find"], rule["replace"], rule.get("comment"))
            count += n
        return count

    def _apply_one_rule(self, find: str, replace: str, comment: str | None) -> int:
        body = self.doc_root.find(qn("w:body"))
        if body is None:
            return 0
        count = 0
        for para in body.iter(qn("w:p")):
            while True:
                result = self._find_in_paragraph(para, find)
                if result is None:
                    break
                self._replace_in_paragraph(para, result, find, replace, comment)
                count += 1
        return count

    def _find_in_paragraph(self, para, find_text: str):
        """在段落中跨 run 搜索文本（跳过已有修订标记内的 run）"""
        runs = list(para.iter(qn("w:r")))
        if not runs:
            return None

        active_runs = []
        for r in runs:
            parent = r.getparent()
            if parent is not None and parent.tag in (qn("w:del"), qn("w:ins")):
                continue
            active_runs.append(r)
        if not active_runs:
            return None

        run_texts = []
        for r in active_runs:
            t_elem = r.find(qn("w:t"))
            run_texts.append(t_elem.text if t_elem is not None and t_elem.text else "")

        full_text = "".join(run_texts)
        idx = full_text.find(find_text)
        if idx == -1:
            return None

        start_pos, end_pos = idx, idx + len(find_text)
        cumulative = 0
        start_run_idx = end_run_idx = None
        start_offset = end_offset = 0

        for i, text in enumerate(run_texts):
            run_start = cumulative
            run_end = cumulative + len(text)
            if start_run_idx is None and run_end > start_pos:
                start_run_idx = i
                start_offset = start_pos - run_start
            if run_end >= end_pos:
                end_run_idx = i
                end_offset = end_pos - run_start
                break
            cumulative = run_end

        if start_run_idx is None or end_run_idx is None:
            return None

        return {
            "runs": active_runs[start_run_idx : end_run_idx + 1],
            "start_offset": start_offset,
            "end_offset": end_offset,
        }

    def _replace_in_paragraph(self, para, match, find_text, replace_text, comment_text):
        """拆分 run，插入 del/ins 标记，保持原有格式"""
        runs = match["runs"]
        start_offset = match["start_offset"]
        end_offset = match["end_offset"]

        # 继承第一个 run 的格式
        rpr_template = runs[0].find(qn("w:rPr"))
        if rpr_template is not None:
            rpr_template = copy.deepcopy(rpr_template)

        # 前缀文本（第一个 run 中匹配之前的部分）
        first_t = runs[0].find(qn("w:t"))
        first_text = first_t.text if first_t is not None and first_t.text else ""
        prefix_text = first_text[:start_offset]

        # 后缀文本（最后一个 run 中匹配之后的部分）
        last_t = runs[-1].find(qn("w:t"))
        last_text = last_t.text if last_t is not None and last_t.text else ""
        suffix_text = last_text[end_offset:]

        # 记录插入位置，删除原 run
        parent = runs[0].getparent()
        insert_pos = list(parent).index(runs[0])
        for r in runs:
            r.getparent().remove(r)

        # 构建替换节点
        nodes = []

        if prefix_text:
            nodes.append(self._make_run(prefix_text, rpr_template))

        # 批注起始
        comment_id = None
        if comment_text:
            comment_id = self._next_comment_id()
            cs = etree.Element(qn("w:commentRangeStart"))
            cs.set(qn("w:id"), str(comment_id))
            nodes.append(cs)

        # <w:del>
        rid = self._next_rid()
        del_node = etree.Element(qn("w:del"))
        del_node.set(qn("w:id"), rid)
        del_node.set(qn("w:author"), self.author)
        del_node.set(qn("w:date"), self.date)
        del_node.append(self._make_del_run(find_text, rpr_template))
        nodes.append(del_node)

        # <w:ins>
        ins_node = etree.Element(qn("w:ins"))
        ins_node.set(qn("w:id"), self._next_rid())
        ins_node.set(qn("w:author"), self.author)
        ins_node.set(qn("w:date"), self.date)
        ins_node.append(self._make_run(replace_text, rpr_template))
        nodes.append(ins_node)

        # 批注结束 + 引用
        if comment_text and comment_id is not None:
            ce = etree.Element(qn("w:commentRangeEnd"))
            ce.set(qn("w:id"), str(comment_id))
            nodes.append(ce)

            ref_run = etree.Element(qn("w:r"))
            ref_rpr = etree.SubElement(ref_run, qn("w:rPr"))
            ref_style = etree.SubElement(ref_rpr, qn("w:rStyle"))
            ref_style.set(qn("w:val"), "CommentReference")
            ref_elem = etree.SubElement(ref_run, qn("w:commentReference"))
            ref_elem.set(qn("w:id"), str(comment_id))
            nodes.append(ref_run)

            self.comments.append(
                {
                    "id": comment_id,
                    "author": self.author,
                    "date": self.date,
                    "text": comment_text,
                }
            )

        if suffix_text:
            nodes.append(self._make_run(suffix_text, rpr_template))

        for i, node in enumerate(nodes):
            parent.insert(insert_pos + i, node)

    def _make_run(self, text: str, rpr=None) -> etree._Element:
        """创建 <w:r>，继承原有 rPr 格式"""
        run = etree.Element(qn("w:r"))
        if rpr is not None:
            run.append(copy.deepcopy(rpr))
        t = etree.SubElement(run, qn("w:t"))
        t.text = text
        t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return run

    def _make_del_run(self, text: str, rpr=None) -> etree._Element:
        """创建 <w:del> 内部的 run（用 <w:delText>）"""
        run = etree.Element(qn("w:r"))
        if rpr is not None:
            run.append(copy.deepcopy(rpr))
        dt = etree.SubElement(run, qn("w:delText"))
        dt.text = text
        dt.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
        return run

    def _write_comments_xml(self):
        if not self.comments:
            return

        comments_path = os.path.join(self.tmpdir, "word", "comments.xml")
        if os.path.exists(comments_path):
            ctree = etree.parse(comments_path)
            croot = ctree.getroot()
        else:
            croot = etree.Element(qn("w:comments"), nsmap={"w": W, "r": R_NS})

        for c in self.comments:
            ce = etree.SubElement(croot, qn("w:comment"))
            ce.set(qn("w:id"), str(c["id"]))
            ce.set(qn("w:author"), c["author"])
            ce.set(qn("w:date"), c["date"])
            ce.set(qn("w:initials"), c["author"][:2])

            p = etree.SubElement(ce, qn("w:p"))
            etree.SubElement(p, qn("w:pPr"))
            r = etree.SubElement(p, qn("w:r"))
            rpr = etree.SubElement(r, qn("w:rPr"))
            rs = etree.SubElement(rpr, qn("w:rStyle"))
            rs.set(qn("w:val"), "CommentReference")
            etree.SubElement(r, qn("w:annotationRef"))

            r2 = etree.SubElement(p, qn("w:r"))
            t = etree.SubElement(r2, qn("w:t"))
            t.text = c["text"]
            t.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

        with open(comments_path, "wb") as f:
            f.write(etree.tostring(croot, xml_declaration=True, encoding="UTF-8", standalone=True))
        self._ensure_content_type("comments")
        self._ensure_rels("comments")

    def _ensure_content_type(self, part: str):
        ct_path = os.path.join(self.tmpdir, "[Content_Types].xml")
        ct_tree = etree.parse(ct_path)
        ct_root = ct_tree.getroot()
        ct_ns = "http://schemas.openxmlformats.org/package/2006/content-types"

        if part == "comments":
            part_name = "/word/comments.xml"
            ct = "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
            for o in ct_root.iter(f"{{{ct_ns}}}Override"):
                if o.get("PartName") == part_name:
                    return
            o = etree.SubElement(ct_root, f"{{{ct_ns}}}Override")
            o.set("PartName", part_name)
            o.set("ContentType", ct)
            with open(ct_path, "wb") as f:
                f.write(etree.tostring(ct_tree, xml_declaration=True, encoding="UTF-8", standalone=True))

    def _ensure_rels(self, part: str):
        rels_path = os.path.join(self.tmpdir, "word", "_rels", "document.xml.rels")
        rels_tree = etree.parse(rels_path)
        rels_root = rels_tree.getroot()
        rels_ns = "http://schemas.openxmlformats.org/package/2006/relationships"

        if part == "comments":
            for rel in rels_root.iter(f"{{{rels_ns}}}Relationship"):
                if rel.get("Type") == REL_COMMENTS:
                    return
            max_id = 0
            for rel in rels_root.iter(f"{{{rels_ns}}}Relationship"):
                m = re.search(r"(\d+)", rel.get("Id", "rId0"))
                if m:
                    max_id = max(max_id, int(m.group(1)))
            new_rel = etree.SubElement(rels_root, f"{{{rels_ns}}}Relationship")
            new_rel.set("Id", f"rId{max_id + 1}")
            new_rel.set("Type", REL_COMMENTS)
            new_rel.set("Target", "comments.xml")
            with open(rels_path, "wb") as f:
                f.write(etree.tostring(rels_tree, xml_declaration=True, encoding="UTF-8", standalone=True))

    def save(self, output_path: str):
        """保存修改后的 .docx"""
        doc_path = os.path.join(self.tmpdir, "word", "document.xml")
        with open(doc_path, "wb") as f:
            f.write(etree.tostring(self.doc_tree, xml_declaration=True, encoding="UTF-8", standalone=True))
        self._write_comments_xml()

        output_path = os.path.abspath(output_path)
        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(self.tmpdir):
                for fn in files:
                    abs_path = os.path.join(root, fn)
                    zf.write(abs_path, os.path.relpath(abs_path, self.tmpdir))
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def cleanup(self):
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)


def review_docx(input_path: str, output_path: str, rules: list[dict], author: str = "CC审阅") -> int:
    """便捷函数：对 .docx 应用替换规则，输出带修订标记的新文件。"""
    reviewer = DocxReviewer(input_path, author=author)
    try:
        count = reviewer.apply_rules(rules)
        reviewer.save(output_path)
        return count
    except Exception:
        reviewer.cleanup()
        raise


# ═══════════════════════════════════════════════════════════════════
#  CLI 入口
# ═══════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(
        description="Word 审阅修订工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="子命令")

    rp = sub.add_parser("read", help="读取修订和批注")
    rp.add_argument("input", help="输入 .docx 文件")
    rp.add_argument("--format", "-f", choices=["md", "json"], default="md", help="输出格式 (默认: md)")

    wp = sub.add_parser("review", help="写入修订标记")
    wp.add_argument("input", help="输入 .docx 文件")
    wp.add_argument("--output", "-o", required=True, help="输出 .docx 文件")
    wp.add_argument("--rules", "-r", required=True, help="替换规则 JSON 文件")
    wp.add_argument("--author", "-a", default="CC审阅", help="作者名")

    cp = sub.add_parser("compare", help="对比生成修订 (v2)")
    cp.add_argument("original", help="原始 .docx")
    cp.add_argument("modified", help="修改后 .docx")
    cp.add_argument("--output", "-o", required=True, help="输出 .docx")

    args = parser.parse_args()

    if args.command == "read":
        print(read_track_changes(args.input, args.format))
    elif args.command == "review":
        with open(args.rules, encoding="utf-8") as f:
            rules = json.load(f)
        count = review_docx(args.input, args.output, rules, author=args.author)
        print(f"完成：{count} 处替换已写入 {args.output}")
    elif args.command == "compare":
        print("compare 功能将在 v2 实现。")
        sys.exit(1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
