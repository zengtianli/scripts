#!/usr/bin/env python3
"""build_site.py — 三阶段知识看板构建器

用法：
    python3 build_site.py <source_dir> [output_dir]

三阶段管线：
    Phase 1: COLLECT → 扫描 MD、解析 frontmatter、提取元数据
    Phase 2: ENRICH  → 关键词 TF-IDF、余弦相似度、统计
    Phase 3: RENDER  → Dashboard、详情页、图谱页、目录索引

纯 Python 3，无第三方依赖（D3 走 CDN）。
"""

import json
import math
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════

IGNORE_DIRS = {".git", "_site", "__pycache__", "node_modules", ".DS_Store"}

CATEGORY_COLORS = {
    "sessions": "#3b82f6",
    "knowledge": "#10b981",
    "memory": "#8b5cf6",
    "projects": "#f59e0b",
    "architecture": "#06b6d4",
    "discussions": "#f97316",
    "decisions": "#ef4444",
    "_archive": "#6b7280",
    "guides": "#14b8a6",
    "cc-memory": "#a855f7",
    "cc-sessions": "#0ea5e9",
}

# CC Memory type 颜色映射
CC_MEMORY_TYPE_COLORS = {
    "feedback": "#10b981",  # 绿
    "project": "#3b82f6",  # 蓝
    "user": "#f59e0b",  # 黄
    "reference": "#06b6d4",  # 青
    "MEMORY.md": "#a855f7",  # 紫
}
DEFAULT_CATEGORY_COLOR = "#64748b"

PROJECT_MAP = {
    "scripts": {"cc_memory": "project_scripts.md", "icon": "terminal"},
    "website": {"cc_memory": "project_website.md", "icon": "globe"},
    "resume": {"cc_memory": "project_resume.md", "icon": "briefcase"},
    "essays": {"cc_memory": None, "icon": "book"},
    "zdwp": {"cc_memory": "project_zdwp.md", "icon": "droplet"},
}

PROJECT_ICONS = {
    "terminal": "\u2328",  # ⌨
    "globe": "\U0001f310",  # 🌐
    "briefcase": "\U0001f4bc",  # 💼
    "book": "\U0001f4da",  # 📚
    "droplet": "\U0001f4a7",  # 💧
    "archive": "\U0001f4e6",  # 📦
}

STOP_WORDS = {
    "the",
    "is",
    "and",
    "to",
    "of",
    "a",
    "in",
    "for",
    "on",
    "it",
    "that",
    "with",
    "as",
    "this",
    "was",
    "are",
    "be",
    "at",
    "from",
    "or",
    "an",
    "by",
    "not",
    "but",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "may",
    "might",
    "can",
    "been",
    "being",
    "were",
    "which",
    "their",
    "what",
    "there",
    "when",
    "than",
    "other",
    "its",
    "into",
    "some",
    "these",
    "them",
    "then",
    "two",
    "no",
    "my",
    "more",
}


# ═══════════════════════════════════════════
# Phase 1: COLLECT
# ═══════════════════════════════════════════


def parse_frontmatter(text):
    """解析 YAML frontmatter（纯 Python，不依赖 yaml）。

    Returns:
        (metadata_dict, body_without_frontmatter)
    """
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        return {}, text

    raw = m.group(1)
    meta = {}
    for line in raw.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()
        # 处理 tags: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",") if v.strip()]
        meta[key] = val

    body = text[m.end() :]
    return meta, body


def collect_all_docs(src_dir):
    """扫描所有 MD 文件，返回文档字典列表。"""
    src = Path(src_dir).resolve()
    docs = []

    for md_path in sorted(src.rglob("*.md")):
        if not md_path.exists():
            continue
        rel = md_path.relative_to(src)
        # 跳过忽略目录
        if any(part in IGNORE_DIRS for part in rel.parts):
            continue

        try:
            raw_text = md_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        meta, body = parse_frontmatter(raw_text)

        # title: frontmatter > 第一个 # 标题 > 文件名
        title = meta.get("title", "")
        if not title:
            h1 = re.search(r"^#\s+(.+)$", raw_text, re.MULTILINE)
            title = h1.group(1).strip() if h1 else rel.stem

        # category: 顶级目录
        category = rel.parts[0] if len(rel.parts) > 1 else ""

        # mtime
        mtime = md_path.stat().st_mtime

        # description
        desc = meta.get("description", "")
        if not desc:
            # 取正文第一段非空行（去掉 heading）
            for line in body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("---"):
                    desc = line[:100]
                    break

        # tags
        tags = meta.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        # headings
        headings = []
        for hm in re.finditer(r"^(#{1,4})\s+(.+)$", body, re.MULTILINE):
            level = len(hm.group(1))
            headings.append((level, hm.group(2).strip()))

        # word_count: 简单估算（中文按字符数，英文按空格分词）
        clean = re.sub(r"[#*`\[\]()>|\-_=~]", " ", body)
        word_count = len(clean.split())

        docs.append(
            {
                "rel_path": str(rel),
                "title": title,
                "category": category,
                "mtime": mtime,
                "description": desc,
                "tags": tags,
                "headings": headings,
                "word_count": word_count,
                "body": body,
            }
        )

    return docs


def collect_project_status(cc_memories):
    """从 PROJECT_MAP + cc_memories 读取项目状态。"""
    # 建立 cc_memories 按 filename 索引
    mem_by_name = {m["filename"]: m for m in (cc_memories or [])}
    projects = []

    for name, info in PROJECT_MAP.items():
        status = "in_progress"
        color = "#f59e0b"
        description = ""
        href = ""

        cc_mem = mem_by_name.get(info["cc_memory"]) if info["cc_memory"] else None
        if cc_mem:
            description = cc_mem["description"][:120]
            href = cc_mem["html_rel"]
            # 简单状态判断
            desc_lower = description.lower()
            if "废弃" in desc_lower or "deprecated" in desc_lower:
                status = "deprecated"
                color = "#6b7280"
            elif "active" in desc_lower or "活跃" in desc_lower:
                status = "active"
                color = "#10b981"

        projects.append(
            {
                "name": name,
                "icon": PROJECT_ICONS.get(info["icon"], "\U0001f4c4"),
                "status": status,
                "color": color,
                "description": description,
                "href": href,
            }
        )

    return projects


def collect_cc_memory(cc_dir):
    """扫描 CC projects/*/memory/*.md，返回 memory 文件列表。"""
    cc = Path(cc_dir).resolve()
    projects_dir = cc / "projects"
    if not projects_dir.exists():
        return []

    memories = []
    for md_path in sorted(projects_dir.rglob("memory/*.md")):
        try:
            raw_text = md_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue

        meta, body = parse_frontmatter(raw_text)
        # 项目名：从路径提取
        rel_to_projects = md_path.relative_to(projects_dir)
        project_name = rel_to_projects.parts[0] if len(rel_to_projects.parts) > 1 else "unknown"
        # 简化项目名
        display_project = project_name.replace("-Users-tianli-", "").replace("-Users-tianli", "~") or "~"

        # 类型：从 frontmatter 的 type 字段
        mem_type = meta.get("type", "")
        if md_path.name == "MEMORY.md":
            mem_type = "MEMORY.md"

        title = meta.get("name", "") or meta.get("title", "") or md_path.stem
        description = meta.get("description", "")
        if not description:
            for line in body.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("---"):
                    description = line[:120]
                    break

        # HTML 相对路径（用于详情页）
        html_rel = f"cc-memory/{display_project}/{md_path.stem}.html"

        memories.append(
            {
                "path": str(md_path),
                "filename": md_path.name,
                "project": display_project,
                "type": mem_type,
                "title": title,
                "description": description,
                "mtime": md_path.stat().st_mtime,
                "word_count": len(body.split()),
                "color": CC_MEMORY_TYPE_COLORS.get(mem_type, "#64748b"),
                "body": body,
                "html_rel": html_rel,
                "tags": [t.strip() for t in str(meta.get("tags", "")).split(",") if t.strip()]
                if meta.get("tags")
                else [],
                "headings": [
                    (len(hm.group(1)), hm.group(2).strip())
                    for hm in re.finditer(r"^(#{1,4})\s+(.+)$", body, re.MULTILINE)
                ],
            }
        )

    return memories


def collect_cc_sessions(cc_dir):
    """从 session_index.json 读取 CC 会话列表。"""
    cc = Path(cc_dir).resolve()
    index_path = cc / "session_index.json"
    if not index_path.exists():
        return []

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def detect_duplicates(docs, cc_memories):
    """检测 docs/memory/ 与 cc-memory 之间的重复/相似文件。"""
    # 收集 docs 中的 memory 文件
    doc_mems = {d["rel_path"]: d for d in docs if d["category"] == "memory"}
    duplicates = []

    for cc_mem in cc_memories:
        cc_name = cc_mem["filename"].lower()
        cc_title = cc_mem["title"].lower()
        for rel_path, doc in doc_mems.items():
            doc_name = Path(rel_path).name.lower()
            doc_title = doc["title"].lower()
            # 同名文件
            if cc_name == doc_name:
                duplicates.append(
                    {
                        "cc_file": cc_mem["filename"],
                        "cc_project": cc_mem["project"],
                        "cc_href": cc_mem["html_rel"],
                        "doc_file": rel_path,
                        "doc_href": _html_path(rel_path),
                        "reason": "同名文件",
                        "cc_title": cc_mem["title"],
                        "doc_title": doc["title"],
                    }
                )
                continue
            # 标题相似（简单 Jaccard）
            cc_words = set(cc_title.split())
            doc_words = set(doc_title.split())
            if cc_words and doc_words:
                jaccard = len(cc_words & doc_words) / len(cc_words | doc_words)
                if jaccard > 0.6:
                    duplicates.append(
                        {
                            "cc_file": cc_mem["filename"],
                            "cc_project": cc_mem["project"],
                            "cc_href": cc_mem["html_rel"],
                            "doc_file": rel_path,
                            "doc_href": _html_path(rel_path),
                            "reason": f"标题相似 ({jaccard:.0%})",
                            "cc_title": cc_mem["title"],
                            "doc_title": doc["title"],
                        }
                    )

    return duplicates


# ═══════════════════════════════════════════
# Phase 2: ENRICH
# ═══════════════════════════════════════════


def tokenize(text):
    """对文本分词：中文 2-gram/3-gram + 英文空格分词 + 停用词过滤。"""
    tokens = []
    # 分离中英文片段
    segments = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", text.lower())
    for seg in segments:
        if re.match(r"^[\u4e00-\u9fff]+$", seg):
            # 中文: 2-gram + 3-gram
            for n in (2, 3):
                for i in range(len(seg) - n + 1):
                    tokens.append(seg[i : i + n])
        else:
            # 英文
            if seg not in STOP_WORDS and len(seg) > 1:
                tokens.append(seg)
    return tokens


def compute_tfidf(docs):
    """计算 TF-IDF，每篇取 top 15 关键词。返回 {rel_path: [(word, score), ...]}。"""
    N = len(docs)
    if N == 0:
        return {}

    # 每篇文档的词频
    doc_tf = {}
    doc_tokens = {}
    df = defaultdict(int)

    for doc in docs:
        text = doc["title"] + " " + doc["body"]
        tokens = tokenize(text)
        doc_tokens[doc["rel_path"]] = tokens
        total = len(tokens)
        if total == 0:
            doc_tf[doc["rel_path"]] = {}
            continue
        freq = defaultdict(int)
        for t in tokens:
            freq[t] += 1
        tf = {t: c / total for t, c in freq.items()}
        doc_tf[doc["rel_path"]] = tf
        for t in freq:
            df[t] += 1

    # 计算 TF-IDF
    keywords = {}
    for doc in docs:
        rp = doc["rel_path"]
        tf = doc_tf[rp]
        scored = []
        for t, tf_val in tf.items():
            idf = math.log(N / (df[t] + 1)) + 1
            scored.append((t, tf_val * idf))
        scored.sort(key=lambda x: -x[1])
        keywords[rp] = scored[:15]

    return keywords


def compute_similarity(docs, keywords):
    """基于 TF-IDF 向量计算余弦相似度，每篇取 top 5 相关文档。

    Returns:
        similar: {rel_path: [(other_rel_path, score), ...]}
        edges: [(source, target, similarity)]  用于 graph_data
    """
    # 构建稀疏向量
    vectors = {}
    for doc in docs:
        rp = doc["rel_path"]
        kw = keywords.get(rp, [])
        vectors[rp] = {w: s for w, s in kw}

    # 计算所有配对的余弦相似度
    rps = [d["rel_path"] for d in docs]
    similar = defaultdict(list)
    edges = []

    for i in range(len(rps)):
        for j in range(i + 1, len(rps)):
            v1 = vectors[rps[i]]
            v2 = vectors[rps[j]]
            # 交集
            common = set(v1.keys()) & set(v2.keys())
            if not common:
                continue
            dot = sum(v1[k] * v2[k] for k in common)
            mag1 = math.sqrt(sum(v**2 for v in v1.values()))
            mag2 = math.sqrt(sum(v**2 for v in v2.values()))
            if mag1 == 0 or mag2 == 0:
                continue
            sim = dot / (mag1 * mag2)
            if sim > 0.1:
                similar[rps[i]].append((rps[j], sim))
                similar[rps[j]].append((rps[i], sim))
                edges.append((rps[i], rps[j], sim))

    # 每篇只保留 top 5
    for rp in similar:
        similar[rp].sort(key=lambda x: -x[1])
        similar[rp] = similar[rp][:5]

    return dict(similar), edges


def compute_stats(docs):
    """计算全站统计。"""
    now = datetime.now().timestamp()
    d7 = now - 7 * 86400
    d14 = now - 14 * 86400
    d30 = now - 30 * 86400

    cat_counts = defaultdict(int)
    total_words = 0
    recent_7d = 0
    recent_14d = 0
    recent_30d = 0

    for doc in docs:
        cat = doc["category"] or "root"
        cat_counts[cat] += 1
        total_words += doc["word_count"]
        if doc["mtime"] >= d7:
            recent_7d += 1
        if doc["mtime"] >= d14:
            recent_14d += 1
        if doc["mtime"] >= d30:
            recent_30d += 1

    return {
        "total_docs": len(docs),
        "category_counts": dict(cat_counts),
        "recent_7d": recent_7d,
        "recent_14d": recent_14d,
        "recent_30d": recent_30d,
        "total_words": total_words,
    }


# ═══════════════════════════════════════════
# MD → HTML 转换
# ═══════════════════════════════════════════


def slugify(text):
    """生成 heading ID。"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\u4e00-\u9fff-]", "-", text.lower())
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "heading"


def strip_frontmatter(text):
    """剥离 frontmatter（如果有的话）。"""
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL)


def md_to_html(md_text, add_heading_ids=False):
    """简易 MD → HTML 转换，纯 Python 无依赖。"""
    html = strip_frontmatter(md_text)

    # 保存代码块
    code_blocks = []

    def save_code(m):
        lang = m.group(1) or ""
        code = m.group(2).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        code_blocks.append(code)
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    html = re.sub(r"```(\w*)\n(.*?)```", save_code, html, flags=re.DOTALL)

    # 保存行内代码
    inline_codes = []

    def save_inline(m):
        code = m.group(1).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        inline_codes.append(code)
        return f"__INLINE_CODE_{len(inline_codes) - 1}__"

    html = re.sub(r"`([^`]+)`", save_inline, html)

    # 表格
    def convert_table(m):
        lines = m.group(0).strip().split("\n")
        rows = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if i == 1 and all(re.match(r"^[-:]+$", c) for c in cells):
                continue
            tag = "th" if i == 0 else "td"
            row = "".join(f"<{tag}>{c}</{tag}>" for c in cells)
            rows.append(f"<tr>{row}</tr>")
        return f"<table>{''.join(rows)}</table>"

    html = re.sub(r"(\|.+\|[\n\r]+)+", convert_table, html)

    # 用于跟踪 heading slug 计数避免重复
    slug_counts = {}

    def make_heading(level):
        def replacer(m):
            text = m.group(1)
            if add_heading_ids:
                slug = slugify(text)
                count = slug_counts.get(slug, 0)
                slug_counts[slug] = count + 1
                unique_slug = slug if count == 0 else f"{slug}-{count}"
                return f'<h{level} id="{unique_slug}">{text}</h{level}>'
            return f"<h{level}>{text}</h{level}>"

        return replacer

    # Headers (从大到小，避免误匹配)
    html = re.sub(r"^#### (.+)$", make_heading(4), html, flags=re.MULTILINE)
    html = re.sub(r"^### (.+)$", make_heading(3), html, flags=re.MULTILINE)
    html = re.sub(r"^## (.+)$", make_heading(2), html, flags=re.MULTILINE)
    html = re.sub(r"^# (.+)$", make_heading(1), html, flags=re.MULTILINE)

    # Bold, italic, strikethrough
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", html)
    html = re.sub(r"~~(.+?)~~", r"<del>\1</del>", html)

    # Checkbox
    html = re.sub(r"- \[x\]", r'<li><input type="checkbox" checked disabled>', html)
    html = re.sub(r"- \[ \]", r'<li><input type="checkbox" disabled>', html)

    # Unordered lists
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

    # Ordered lists
    html = re.sub(r"^\d+\. (.+)$", r"<li>\1</li>", html, flags=re.MULTILINE)

    # Blockquote
    html = re.sub(r"^> (.+)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

    # HR
    html = re.sub(r"^---+$", r"<hr>", html, flags=re.MULTILINE)

    # Images
    html = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r'<img src="\2" alt="\1">', html)

    # Links
    html = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', html)

    # Paragraphs
    lines = html.split("\n")
    result = []
    for line in lines:
        stripped = line.strip()
        if (
            stripped
            and not stripped.startswith("<")
            and not stripped.startswith("__CODE")
            and not stripped.startswith("__INLINE")
        ):
            result.append(f"<p>{line}</p>")
        else:
            result.append(line)
    html = "\n".join(result)

    # 还原代码块
    for i, block in enumerate(code_blocks):
        html = html.replace(f"__CODE_BLOCK_{i}__", f"<pre><code>{block}</code></pre>")
    for i, code in enumerate(inline_codes):
        html = html.replace(f"__INLINE_CODE_{i}__", f"<code>{code}</code>")

    return html


# ═══════════════════════════════════════════
# Phase 3: RENDER — 共用 CSS / 工具
# ═══════════════════════════════════════════


def _cat_color(cat):
    return CATEGORY_COLORS.get(cat, DEFAULT_CATEGORY_COLOR)


def _format_date(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")


def _format_datetime(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")


def _html_path(rel_path):
    """MD 的相对路径 → HTML 的相对路径。"""
    return str(Path(rel_path).with_suffix(".html"))


def _tags_html(tags, small=False):
    if not tags:
        return ""
    size = "font-size:0.7em;padding:2px 6px;" if small else "font-size:0.75em;padding:2px 8px;"
    pills = "".join(
        f'<span style="display:inline-block;background:#e0e7ff;color:#3730a3;border-radius:9999px;{size}margin:2px;">{t}</span>'
        for t in tags[:6]
    )
    return pills


SHARED_CSS = """
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;
  line-height:1.6;color:#1e293b;background:var(--bg-secondary,#f8fafc)}
:root{
  --bg-primary:#0f172a;--bg-secondary:#f8fafc;--bg-card:#ffffff;
  --text-primary:#1e293b;--text-secondary:#64748b;
  --accent-blue:#3b82f6;--border:#e2e8f0;
}
a{color:#3b82f6;text-decoration:none}
a:hover{text-decoration:underline}

/* Header */
.site-header{background:var(--bg-primary);color:#fff;padding:1rem 2rem;
  display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem}
.site-header h1{font-size:1.3rem;font-weight:700;letter-spacing:-0.02em}
.site-header a{color:#93c5fd;text-decoration:none}
.site-header a:hover{color:#fff}
.header-stats{display:flex;gap:1.5rem;font-size:0.85rem;color:#94a3b8}
.header-stats .stat-val{color:#fff;font-weight:700;font-size:1.1rem}

/* Card */
.card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;
  box-shadow:0 1px 3px rgba(0,0,0,.1);padding:1.25rem;margin-bottom:1rem}

/* Pill / badge */
.cat-pill{display:inline-block;border-radius:9999px;padding:2px 10px;font-size:0.75rem;
  color:#fff;font-weight:600;line-height:1.6}

/* Container */
.container{max-width:1200px;margin:0 auto;padding:1.5rem 2rem}

/* Grid layouts */
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:1.5rem}
.grid-full{grid-column:1/-1}
@media(max-width:768px){.grid-2{grid-template-columns:1fr}}

/* Table */
table{border-collapse:collapse;width:100%;margin:0.8rem 0}
th,td{border:1px solid #d1d5db;padding:0.5rem 0.75rem;text-align:left}
th{background:#f3f4f6;font-weight:600}
tr:nth-child(even){background:#f9fafb}

/* Code */
code{background:#f3f4f6;padding:0.15rem 0.4rem;border-radius:4px;font-size:0.9em}
pre{background:#1f2937;color:#f9fafb;padding:1rem;border-radius:8px;overflow-x:auto;margin:0.8rem 0}
pre code{background:none;padding:0;color:inherit}

/* Lists */
ul,ol{padding-left:1.5rem;margin:0.5rem 0}
li{margin:0.2rem 0}

/* Blockquote */
blockquote{border-left:4px solid #3b82f6;padding:0.5rem 1rem;margin:0.8rem 0;background:#eff6ff;color:#1e40af}

/* Headings */
h1{font-size:1.8rem;border-bottom:2px solid #e5e7eb;padding-bottom:0.5rem;margin:1.5rem 0 1rem;color:#111827}
h2{font-size:1.4rem;border-bottom:1px solid #e5e7eb;padding-bottom:0.3rem;margin:1.3rem 0 0.8rem;color:#1f2937}
h3{font-size:1.15rem;margin:1rem 0 0.5rem;color:#374151}
h4{font-size:1.05rem;margin:0.8rem 0 0.4rem;color:#4b5563}
p{margin:0.5rem 0}
hr{border:none;border-top:1px solid #e5e7eb;margin:1.5rem 0}
img{max-width:100%;height:auto}
input[type="checkbox"]{margin-right:0.3rem}

/* Footer */
.footer{text-align:center;color:#9ca3af;font-size:0.8em;margin-top:3rem;padding-top:1rem;border-top:1px solid var(--border)}

/* Module section */
.module-title{font-size:1.1rem;font-weight:700;color:var(--text-primary);margin-bottom:0.75rem;
  display:flex;align-items:center;justify-content:space-between}

/* Button group */
.btn-group{display:flex;gap:4px}
.btn-group button{border:1px solid var(--border);background:var(--bg-card);color:var(--text-secondary);
  border-radius:6px;padding:3px 10px;font-size:0.8rem;cursor:pointer;transition:all .15s}
.btn-group button.active,
.btn-group button:hover{background:var(--accent-blue);color:#fff;border-color:var(--accent-blue)}

/* Doc card */
.doc-card{border-bottom:1px solid var(--border);padding:0.75rem 0}
.doc-card:last-child{border-bottom:none}
.doc-card-title{font-weight:600;color:var(--text-primary)}
.doc-card-desc{font-size:0.85em;color:var(--text-secondary);margin-top:2px}
.doc-card-meta{font-size:0.8em;color:var(--text-secondary);margin-top:4px;display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap}

/* Project cards grid */
.proj-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem}
@media(max-width:768px){.proj-grid{grid-template-columns:repeat(2,1fr)}}
.proj-card{background:var(--bg-card);border:1px solid var(--border);border-radius:12px;
  box-shadow:0 1px 3px rgba(0,0,0,.1);padding:1rem;display:flex;flex-direction:column;gap:0.4rem;transition:transform .1s,box-shadow .1s}
.proj-icon{font-size:1.6rem}
.proj-name{font-weight:700;display:flex;align-items:center;gap:0.5rem}
.proj-status{display:inline-block;width:8px;height:8px;border-radius:50%}
.proj-desc{font-size:0.82em;color:var(--text-secondary)}

/* Activity table */
.activity-table{width:100%;border-collapse:collapse}
.activity-table td,.activity-table th{padding:0.6rem 0.8rem;border-bottom:1px solid var(--border);text-align:left;font-size:0.9em}
.activity-table tr:hover{background:#f1f5f9}

/* Bar chart */
.bar-row{display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;font-size:0.85em}
.bar-label{width:100px;text-align:right;color:var(--text-secondary);flex-shrink:0}
.bar-track{flex:1;height:22px;background:#e2e8f0;border-radius:6px;overflow:hidden}
.bar-fill{height:100%;border-radius:6px;display:flex;align-items:center;padding-left:6px;
  color:#fff;font-size:0.75rem;font-weight:600;min-width:24px}

/* Graph entry */
.graph-entry{background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;border-radius:12px;
  padding:2rem;display:flex;flex-direction:column;align-items:center;justify-content:center;
  gap:0.5rem;text-align:center;text-decoration:none !important;transition:transform .15s}
.graph-entry:hover{transform:scale(1.02);text-decoration:none !important}
.graph-entry .big{font-size:1.5rem;font-weight:700}

/* Breadcrumb */
.breadcrumb{background:#f1f5f9;padding:0.5rem 2rem;border-bottom:1px solid var(--border);font-size:0.9em}
.breadcrumb a{color:#2563eb}
.breadcrumb span.sep{color:#94a3b8;margin:0 0.3rem}

/* Detail page layout */
.detail-layout{display:flex;gap:2rem}
.detail-toc{width:220px;flex-shrink:0;position:sticky;top:20px;align-self:flex-start;max-height:calc(100vh - 40px);overflow-y:auto}
.detail-toc ul{list-style:none;padding:0}
.detail-toc li{margin:0}
.detail-toc a{display:block;padding:3px 8px;border-left:2px solid transparent;color:var(--text-secondary);
  font-size:0.82em;text-decoration:none;transition:all .15s}
.detail-toc a:hover,.detail-toc a.active{color:var(--accent-blue);border-left-color:var(--accent-blue);background:#eff6ff}
.detail-toc .toc-h3{padding-left:20px}
.detail-toc .toc-h4{padding-left:32px}
.detail-main{flex:1;min-width:0}
.detail-meta{display:flex;align-items:center;gap:0.75rem;flex-wrap:wrap;margin-bottom:1rem;font-size:0.85em;color:var(--text-secondary)}
.related-docs{margin-top:2rem;padding-top:1.5rem;border-top:1px solid var(--border)}
.related-grid{display:flex;gap:1rem;flex-wrap:wrap}
.related-card{flex:1 1 180px;max-width:250px;background:var(--bg-card);border:1px solid var(--border);
  border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,.1);padding:1rem}
.related-card-title{font-weight:600;font-size:0.9em}
.related-card-desc{font-size:0.8em;color:var(--text-secondary);margin-top:4px}
@media(max-width:768px){.detail-layout{flex-direction:column}.detail-toc{display:none}}

/* Directory index */
.dir-section-title{font-size:1rem;color:#374151;margin:1.5rem 0 0.5rem;padding-bottom:0.3rem;border-bottom:1px solid #e5e7eb}
.dir-list{list-style:none;padding:0}
.dir-list li{padding:0.6rem 0.8rem;border-bottom:1px solid #e5e7eb}
.dir-list li:hover{background:#f1f5f9}
.file-list{list-style:none;padding:0}
.file-list li{padding:0.6rem 0.8rem;border-bottom:1px solid #f3f4f6}
.file-list li:hover{background:#f8fafc}
.file-item{display:flex;justify-content:space-between;align-items:flex-start;gap:1rem}
.file-info{flex:1}
.file-title{font-weight:600;color:var(--text-primary)}
.file-desc{font-size:0.82em;color:var(--text-secondary);margin-top:2px}
.file-meta{display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-top:4px}
.file-date{color:#6b7280;font-size:0.82em;white-space:nowrap;flex-shrink:0}

/* Clickable cards & items */
a.cc-mem-card,a.cc-session-item,a.proj-card{text-decoration:none;color:inherit;display:block}
a.cc-mem-card:hover,a.cc-session-item:hover,a.proj-card:hover{text-decoration:none}
a.proj-card:hover{transform:translateY(-2px);box-shadow:0 3px 8px rgba(0,0,0,.1)}
.cc-proj-group{margin-bottom:1.25rem}
.cc-proj-name{font-weight:700;font-size:0.95rem;margin-bottom:0.5rem;color:var(--text-primary)}
.cc-proj-count{font-weight:400;color:var(--text-secondary);font-size:0.85em}
.cc-mem-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:0.75rem}
.cc-mem-card{background:var(--bg-card);border:1px solid var(--border);border-radius:10px;padding:0.75rem;
  box-shadow:0 1px 2px rgba(0,0,0,.06);transition:transform .1s}
.cc-mem-card:hover{transform:translateY(-2px);box-shadow:0 3px 8px rgba(0,0,0,.1)}
.cc-mem-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:0.4rem}
.cc-mem-type{display:inline-block;border-radius:9999px;padding:1px 8px;font-size:0.7rem;color:#fff;font-weight:600}
.cc-mem-date{font-size:0.75em;color:var(--text-secondary)}
.cc-mem-title{font-weight:600;font-size:0.88rem;color:var(--text-primary);margin-bottom:0.2rem}
.cc-mem-desc{font-size:0.8em;color:var(--text-secondary);line-height:1.4}

/* CC Session timeline */
.cc-session-item{display:flex;gap:1rem;padding:0.6rem 0;border-bottom:1px solid var(--border)}
.cc-session-item:last-child{border-bottom:none}
.cc-session-date{flex-shrink:0;width:90px;font-size:0.82em;color:var(--text-secondary);padding-top:2px}
.cc-session-body{flex:1}
.cc-session-title{font-weight:600;font-size:0.9rem;color:var(--text-primary)}
.cc-session-meta{display:flex;gap:0.6rem;align-items:center;flex-wrap:wrap;margin-top:3px;font-size:0.8em;color:var(--text-secondary)}
.cc-load-more{text-align:center;padding:0.75rem;color:var(--accent-blue);cursor:pointer;font-size:0.9em;
  border-top:1px solid var(--border);margin-top:0.5rem}
.cc-load-more:hover{background:#f1f5f9}

/* Chat bubble */
#cc-chat-bubble{position:fixed;bottom:24px;right:24px;width:56px;height:56px;border-radius:50%;
  background:linear-gradient(135deg,#3b82f6,#6366f1);display:flex;align-items:center;justify-content:center;
  cursor:pointer;box-shadow:0 4px 12px rgba(59,130,246,.4);z-index:9999;transition:transform .15s}
#cc-chat-bubble:hover{transform:scale(1.1)}
#cc-chat-panel{position:fixed;bottom:24px;right:24px;width:380px;height:500px;border-radius:16px;
  background:var(--bg-card);border:1px solid var(--border);box-shadow:0 8px 30px rgba(0,0,0,.15);
  z-index:9999;flex-direction:column;overflow:hidden}
.cc-chat-header{background:linear-gradient(135deg,#3b82f6,#6366f1);color:#fff;padding:0.75rem 1rem;
  display:flex;justify-content:space-between;align-items:center;font-weight:600}
.cc-chat-messages{flex:1;overflow-y:auto;padding:1rem;display:flex;flex-direction:column;gap:0.5rem}
.cc-chat-msg{padding:0.5rem 0.75rem;border-radius:12px;max-width:85%;font-size:0.88em;line-height:1.5;word-break:break-word}
.cc-chat-user{background:#eff6ff;color:#1e40af;align-self:flex-end;border-bottom-right-radius:4px}
.cc-chat-assistant{background:#f1f5f9;color:var(--text-primary);align-self:flex-start;border-bottom-left-radius:4px}
.cc-chat-input{display:flex;gap:0.5rem;padding:0.75rem;border-top:1px solid var(--border)}
.cc-chat-input input{flex:1;border:1px solid var(--border);border-radius:8px;padding:0.5rem 0.75rem;font-size:0.88em;outline:none}
.cc-chat-input input:focus{border-color:var(--accent-blue)}
.cc-chat-input button{background:var(--accent-blue);color:#fff;border:none;border-radius:8px;padding:0.5rem 1rem;
  font-size:0.88em;cursor:pointer;font-weight:600}
.cc-chat-input button:hover{background:#2563eb}
@media(max-width:480px){#cc-chat-panel{width:calc(100vw - 16px);right:8px;bottom:8px;height:60vh}}
</style>
"""


# ═══════════════════════════════════════════
# Phase 3a: Dashboard (index.html)
# ═══════════════════════════════════════════


def render_dashboard(docs, projects, stats, similar, build_time, cc_memories=None, cc_sessions=None, duplicates=None):
    """渲染 Dashboard 首页。"""
    # --- Header ---
    total_cats = len(stats["category_counts"])
    header = f"""<div class="site-header">
  <h1>Tianli's Knowledge Dashboard</h1>
  <div class="header-stats">
    <div><span class="stat-val">{stats["total_docs"]}</span> docs</div>
    <div><span class="stat-val">{stats["total_words"]:,}</span> words</div>
    <div><span class="stat-val">{stats["recent_7d"]}</span> this week</div>
    <div><span class="stat-val">{total_cats}</span> categories</div>
  </div>
</div>"""

    # --- Module 2: 项目进度 ---
    proj_cards = []
    for p in projects:
        tag = "a" if p.get("href") else "div"
        href_attr = f' href="{p["href"]}"' if p.get("href") else ""
        proj_cards.append(f'''<{tag} class="proj-card"{href_attr}>
  <div class="proj-icon">{p["icon"]}</div>
  <div class="proj-name">{p["name"]} <span class="proj-status" style="background:{p["color"]}"></span></div>
  <div class="proj-desc">{p["description"][:100]}</div>
</{tag}>''')
    module2 = f"""<div class="card">
  <div class="module-title">项目进度</div>
  <div class="proj-grid">{"".join(proj_cards)}</div>
</div>"""

    # --- Module 3: 最新文档动态 (全宽, 排除 sessions) ---
    non_session = [d for d in docs if d["category"] != "sessions"]
    non_session.sort(key=lambda d: -d["mtime"])
    rows = []
    for d in non_session:
        col = _cat_color(d["category"])
        cat_label = d["category"] or "root"
        href = _html_path(d["rel_path"])
        desc_trunc = (d["description"][:80] + "...") if len(d["description"]) > 80 else d["description"]
        date_str = _format_date(d["mtime"])
        rows.append(f'''<tr>
  <td><span class="cat-pill" style="background:{col}">{cat_label}</span></td>
  <td><a href="{href}">{d["title"]}</a></td>
  <td style="color:var(--text-secondary);font-size:0.85em">{desc_trunc}</td>
  <td style="color:var(--text-secondary);font-size:0.85em;white-space:nowrap">{date_str}</td>
</tr>''')
    module3 = f"""<div class="card grid-full">
  <div class="module-title">最新文档动态</div>
  <table class="activity-table"><tbody>{"".join(rows)}</tbody></table>
</div>"""

    # --- Module 4: 知识库统计 + 图谱入口 (全宽) ---
    sorted_cats = sorted(stats["category_counts"].items(), key=lambda x: -x[1])
    max_count = max((c for _, c in sorted_cats), default=1)
    bars = []
    for cat, cnt in sorted_cats:
        col = _cat_color(cat)
        pct = max(cnt / max_count * 100, 5)
        bars.append(f"""<div class="bar-row">
  <div class="bar-label">{cat}</div>
  <div class="bar-track"><div class="bar-fill" style="width:{pct:.0f}%;background:{col}">{cnt}</div></div>
</div>""")
    bars_html = "\n".join(bars)

    module4 = f"""<div class="card grid-full" style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem">
  <div>
    <div class="module-title">知识库统计</div>
    {bars_html}
  </div>
  <div style="display:flex;flex-direction:column;gap:1rem;justify-content:center">
    <a class="graph-entry" href="graph.html">
      <div class="big">探索知识图谱 &rarr;</div>
      <div>{stats["total_docs"]} documents &middot; {stats["total_words"]:,} words</div>
    </a>
  </div>
</div>"""

    # --- Module 5: CC 记忆 ---
    module5 = ""
    if cc_memories:
        # 按项目分组
        by_project = defaultdict(list)
        for m in cc_memories:
            by_project[m["project"]].append(m)

        mem_cards = []
        for proj, mems in sorted(by_project.items()):
            proj_cards = []
            for m in sorted(mems, key=lambda x: -x["mtime"]):
                type_color = m["color"]
                type_label = m["type"] or "other"
                date_str = _format_date(m["mtime"])
                href = m["html_rel"]
                proj_cards.append(f'''<a class="cc-mem-card" href="{href}">
  <div class="cc-mem-header">
    <span class="cc-mem-type" style="background:{type_color}">{type_label}</span>
    <span class="cc-mem-date">{date_str}</span>
  </div>
  <div class="cc-mem-title">{m["title"]}</div>
  <div class="cc-mem-desc">{m["description"][:100]}</div>
</a>''')
            mem_cards.append(f"""<div class="cc-proj-group">
  <div class="cc-proj-name">{proj} <span class="cc-proj-count">({len(mems)})</span></div>
  <div class="cc-mem-grid">{"".join(proj_cards)}</div>
</div>""")

        module5 = f"""<div class="card grid-full">
  <div class="module-title">
    <span>CC 记忆 <span style="font-weight:400;font-size:0.85em;color:var(--text-secondary)">({len(cc_memories)} files)</span></span>
  </div>
  {"".join(mem_cards)}
</div>"""

    # --- Module 6: CC 会话时间线（过滤 trivial，显示摘要）---
    module6 = ""
    if cc_sessions:
        # 过滤掉 trivial 会话
        valid_sessions = [s for s in cc_sessions if not s.get("trivial")]
        timeline_items = []
        show_sessions = valid_sessions[:20]

        cat_colors = {
            "开发": "#10b981",
            "配置": "#3b82f6",
            "学习": "#8b5cf6",
            "排查": "#ef4444",
            "写作": "#f59e0b",
            "整理": "#06b6d4",
            "讨论": "#f97316",
        }

        for s in show_sessions:
            proj = s.get("project", "").replace("-Users-tianli-", "").replace("-Users-tianli", "~") or "~"
            title = s.get("title", "Untitled")[:60]
            start = s.get("start_time", "")[:10]
            dur = s.get("duration_minutes", 0)
            msgs = s.get("message_count", 0)
            size = s.get("file_size_kb", 0)
            dur_str = f"{dur}min" if dur else "?"
            sid = s.get("session_id", "")
            s_href = f"cc-sessions/{sid}.html" if sid else "#"

            summary = s.get("summary", "")
            category = s.get("category", "")
            outcomes = s.get("outcomes", "")
            cat_color = cat_colors.get(category, "#64748b")

            # 摘要行
            summary_html = ""
            if summary:
                summary_html = (
                    f'<div style="font-size:0.85em;color:var(--text-secondary);margin-top:3px">{summary}</div>'
                )
            if outcomes and outcomes != "无":
                summary_html += f'<div style="font-size:0.8em;color:#10b981;margin-top:2px">→ {outcomes}</div>'

            # 分类标签
            cat_pill = ""
            if category:
                cat_pill = f'<span class="cat-pill" style="background:{cat_color};font-size:0.7em">{category}</span>'

            timeline_items.append(f'''<a class="cc-session-item" href="{s_href}">
  <div class="cc-session-date">{start}</div>
  <div class="cc-session-body">
    <div class="cc-session-title">{title}</div>
    {summary_html}
    <div class="cc-session-meta">
      <span class="cat-pill" style="background:#0ea5e9;font-size:0.7em">{proj}</span>
      {cat_pill}
      <span>{dur_str}</span>
      <span>{msgs} msgs</span>
      <span>{size} KB</span>
    </div>
  </div>
</a>''')

        remaining = len(valid_sessions) - 20
        load_more = ""
        if remaining > 0:
            load_more = f'<div class="cc-load-more" id="cc-load-more" onclick="loadMoreSessions()">加载更多 ({remaining} 条)</div>'

        trivial_count = len(cc_sessions) - len(valid_sessions)
        module6 = f"""<div class="card grid-full">
  <div class="module-title">
    <span>CC 会话 <span style="font-weight:400;font-size:0.85em;color:var(--text-secondary)">({len(valid_sessions)} 有效 / {trivial_count} 已过滤)</span></span>
  </div>
  <div id="cc-session-list">{"".join(timeline_items)}</div>
  {load_more}
</div>"""

    # --- Module 7: 重复检测（有重复时才显示）---
    module7 = ""
    if duplicates:
        dup_rows = []
        for d in duplicates:
            dup_rows.append(f'''<tr>
  <td><a href="{d["cc_href"]}"><strong>{d["cc_file"]}</strong></a><br><span style="font-size:0.8em;color:var(--text-secondary)">{d["cc_project"]}</span></td>
  <td><a href="{d["doc_href"]}"><strong>{d["doc_title"]}</strong></a><br><span style="font-size:0.8em;color:var(--text-secondary)">{d["doc_file"]}</span></td>
  <td><span class="cat-pill" style="background:#ef4444">{d["reason"]}</span></td>
</tr>''')
        module7 = f"""<div class="card grid-full">
  <div class="module-title" style="color:#ef4444">
    <span>重复检测 <span style="font-weight:400;font-size:0.85em">({len(duplicates)} 对)</span></span>
  </div>
  <p style="font-size:0.85em;color:var(--text-secondary);margin-bottom:0.75rem">以下文件在 docs/memory 和 CC memory 中可能重复，建议通过 Chat 助手合并。</p>
  <table class="activity-table">
    <thead><tr><th>CC Memory</th><th>Docs Memory</th><th>原因</th></tr></thead>
    <tbody>{"".join(dup_rows)}</tbody>
  </table>
</div>"""

    # --- Chat 气泡 ---
    chat_bubble = """
<div id="cc-chat-bubble" onclick="toggleChat()">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2">
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
  </svg>
</div>
<div id="cc-chat-panel" style="display:none">
  <div class="cc-chat-header">
    <span>CC Assistant</span>
    <button onclick="toggleChat()" style="background:none;border:none;color:#fff;font-size:1.2rem;cursor:pointer">&times;</button>
  </div>
  <div id="cc-chat-messages" class="cc-chat-messages"></div>
  <div class="cc-chat-input">
    <input type="text" id="cc-chat-input" placeholder="问点什么..." onkeydown="if(event.key===\'Enter\')sendChat()">
    <button onclick="sendChat()">发送</button>
  </div>
</div>"""

    # --- JS ---
    # 准备全量 session 数据供"加载更多"使用
    all_sessions_json = ""
    if cc_sessions:
        valid_sessions = [s for s in cc_sessions if not s.get("trivial")]
        if len(valid_sessions) > 20:
            remaining_sessions = valid_sessions[20:]
            cat_colors = {
                "开发": "#10b981",
                "配置": "#3b82f6",
                "学习": "#8b5cf6",
                "排查": "#ef4444",
                "写作": "#f59e0b",
                "整理": "#06b6d4",
                "讨论": "#f97316",
            }
            sessions_for_js = []
            for s in remaining_sessions:
                cat = s.get("category", "")
                sessions_for_js.append(
                    {
                        "project": s.get("project", "").replace("-Users-tianli-", "").replace("-Users-tianli", "~")
                        or "~",
                        "title": s.get("title", "Untitled")[:60],
                        "start_time": s.get("start_time", "")[:10],
                        "duration_minutes": s.get("duration_minutes", 0),
                        "message_count": s.get("message_count", 0),
                        "file_size_kb": s.get("file_size_kb", 0),
                        "summary": s.get("summary", ""),
                        "category": cat,
                        "cat_color": cat_colors.get(cat, "#64748b"),
                        "outcomes": s.get("outcomes", ""),
                        "session_id": s.get("session_id", ""),
                    }
                )
            all_sessions_json = json.dumps(sessions_for_js, ensure_ascii=False)

    js = f"""<script>
/* Chat */
var chatHistory = [];
function toggleChat() {{
  var panel = document.getElementById('cc-chat-panel');
  var bubble = document.getElementById('cc-chat-bubble');
  if (panel.style.display === 'none') {{
    panel.style.display = 'flex';
    bubble.style.display = 'none';
    document.getElementById('cc-chat-input').focus();
  }} else {{
    panel.style.display = 'none';
    bubble.style.display = 'flex';
  }}
}}
function appendMsg(role, text) {{
  var msgs = document.getElementById('cc-chat-messages');
  var div = document.createElement('div');
  div.className = 'cc-chat-msg cc-chat-' + role;
  div.innerHTML = text.replace(/\\n/g, '<br>');
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}}
function sendChat() {{
  var input = document.getElementById('cc-chat-input');
  var msg = input.value.trim();
  if (!msg) return;
  input.value = '';
  appendMsg('user', msg);
  chatHistory.push({{role:'user', content:msg}});
  appendMsg('assistant', '<em>思考中...</em>');
  fetch('/api/chat', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{message: msg, history: chatHistory.slice(-10)}})
  }})
  .then(function(r) {{ return r.json(); }})
  .then(function(data) {{
    var msgs = document.getElementById('cc-chat-messages');
    msgs.removeChild(msgs.lastChild);
    var resp = data.response || data.error || 'No response';
    appendMsg('assistant', resp);
    chatHistory.push({{role:'assistant', content:resp}});
  }})
  .catch(function(e) {{
    var msgs = document.getElementById('cc-chat-messages');
    msgs.removeChild(msgs.lastChild);
    appendMsg('assistant', 'Error: ' + e.message);
  }});
}}

/* Load more sessions */
var remainingSessions = {all_sessions_json or "[]"};
function loadMoreSessions() {{
  var list = document.getElementById('cc-session-list');
  var btn = document.getElementById('cc-load-more');
  var batch = remainingSessions.splice(0, 20);
  batch.forEach(function(s) {{
    var dur = s.duration_minutes ? s.duration_minutes + 'min' : '?';
    var summaryHtml = s.summary ? '<div style="font-size:0.85em;color:var(--text-secondary);margin-top:3px">' + s.summary + '</div>' : '';
    if (s.outcomes && s.outcomes !== '无') summaryHtml += '<div style="font-size:0.8em;color:#10b981;margin-top:2px">→ ' + s.outcomes + '</div>';
    var catPill = s.category ? '<span class="cat-pill" style="background:' + s.cat_color + ';font-size:0.7em">' + s.category + '</span>' : '';
    var href = s.session_id ? 'cc-sessions/' + s.session_id + '.html' : '#';
    var html = '<a class="cc-session-item" href="' + href + '">' +
      '<div class="cc-session-date">' + s.start_time + '</div>' +
      '<div class="cc-session-body">' +
        '<div class="cc-session-title">' + s.title + '</div>' +
        summaryHtml +
        '<div class="cc-session-meta">' +
          '<span class="cat-pill" style="background:#0ea5e9;font-size:0.7em">' + s.project + '</span>' +
          catPill +
          '<span>' + dur + '</span>' +
          '<span>' + s.message_count + ' msgs</span>' +
          '<span>' + s.file_size_kb + ' KB</span>' +
        '</div>' +
      '</div>' +
    '</a>';
    list.insertAdjacentHTML('beforeend', html);
  }});
  if (remainingSessions.length === 0) {{
    btn.style.display = 'none';
  }} else {{
    btn.textContent = '加载更多 (' + remainingSessions.length + ' 条)';
  }}
}}
</script>"""

    body = (
        header
        + '\n<div class="container">\n  '
        + module2
        + "\n  "
        + module3
        + "\n  "
        + module4
        + "\n  "
        + module5
        + "\n  "
        + module6
        + "\n  "
        + module7
        + '\n  <div class="footer">Built at '
        + build_time
        + " | CC 产物管理中心</div>"
        + "\n</div>\n"
        + chat_bubble
        + "\n"
        + js
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Tianli's Knowledge Dashboard</title>
{SHARED_CSS}
</head>
<body>
{body}
</body>
</html>"""


# ═══════════════════════════════════════════
# Phase 3a+: CC Memory / Session 详情页
# ═══════════════════════════════════════════


def render_cc_memory_detail(mem, build_time):
    """渲染 CC Memory 的详情页。"""
    depth = len(Path(mem["html_rel"]).parts) - 1
    root_prefix = "../" * depth

    # Breadcrumb
    bc = (
        f'<a href="{root_prefix}index.html">Dashboard</a>'
        f' <span class="sep">/</span> CC Memory'
        f' <span class="sep">/</span> {mem["project"]}'
        f' <span class="sep">/</span> <strong>{mem["filename"]}</strong>'
    )

    # Meta
    col = mem["color"]
    type_label = mem["type"] or "other"
    date_str = _format_datetime(mem["mtime"])
    meta_html = f"""<div class="detail-meta">
  <span class="cat-pill" style="background:{col}">{type_label}</span>
  <span class="cat-pill" style="background:#a855f7">cc-memory</span>
  <span>{date_str}</span>
  <span>{mem["word_count"]} words</span>
  <span>Project: {mem["project"]}</span>
</div>"""

    # TOC sidebar
    toc_html = ""
    if len(mem["headings"]) >= 3:
        toc_items = []
        for level, text in mem["headings"]:
            slug = slugify(text)
            css_class = f"toc-h{level}" if level >= 3 else ""
            toc_items.append(f'<li><a class="{css_class}" href="#{slug}">{text}</a></li>')
        toc_html = f"""<nav class="detail-toc">
  <div style="font-weight:700;font-size:0.85em;color:var(--text-secondary);margin-bottom:0.5rem;padding:0 8px">TABLE OF CONTENTS</div>
  <ul class="toc">{"".join(toc_items)}</ul>
</nav>"""

    body_html = md_to_html(mem["body"], add_heading_ids=True)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{mem["title"]} - CC Memory</title>
{SHARED_CSS}
</head>
<body>
<div class="site-header">
  <a href="{root_prefix}index.html" style="font-weight:700;font-size:1.1rem">Tianli's Knowledge Dashboard</a>
</div>
<div class="breadcrumb">{bc}</div>
<div class="container">
  {meta_html}
  <div class="detail-layout">
    {toc_html}
    <div class="detail-main">
      {body_html}
    </div>
  </div>
  <div class="footer">Built at {build_time} | CC 产物管理中心</div>
</div>
</body>
</html>'''


def render_cc_session_detail(session, build_time):
    """渲染 CC Session 的摘要详情页。"""
    sid = session.get("session_id", "unknown")
    html_rel = f"cc-sessions/{sid}.html"
    depth = len(Path(html_rel).parts) - 1
    root_prefix = "../" * depth

    proj = session.get("project", "").replace("-Users-tianli-", "").replace("-Users-tianli", "~") or "~"
    title = session.get("title", "Untitled")
    start = session.get("start_time", "")
    dur = session.get("duration_minutes", 0)
    msgs = session.get("message_count", 0)
    size = session.get("file_size_kb", 0)
    cwd = session.get("cwd", "")

    bc = (
        f'<a href="{root_prefix}index.html">Dashboard</a>'
        f' <span class="sep">/</span> CC Sessions'
        f' <span class="sep">/</span> <strong>{title[:40]}</strong>'
    )

    # 元数据卡片
    info_rows = [
        ("Session ID", f"<code>{sid}</code>"),
        ("Project", proj),
        ("Start Time", start),
        ("Duration", f"{dur} min" if dur else "Unknown"),
        ("Messages", str(msgs)),
        ("File Size", f"{size} KB"),
        ("Working Directory", f"<code>{cwd}</code>" if cwd else "Unknown"),
    ]
    rows_html = "\n".join(
        f'<tr><td style="font-weight:600;width:160px">{k}</td><td>{v}</td></tr>' for k, v in info_rows
    )

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title[:50]} - CC Session</title>
{SHARED_CSS}
</head>
<body>
<div class="site-header">
  <a href="{root_prefix}index.html" style="font-weight:700;font-size:1.1rem">Tianli's Knowledge Dashboard</a>
</div>
<div class="breadcrumb">{bc}</div>
<div class="container">
  <div class="detail-meta">
    <span class="cat-pill" style="background:#0ea5e9">cc-session</span>
    <span class="cat-pill" style="background:#0ea5e9;font-size:0.75em">{proj}</span>
    <span>{start[:10]}</span>
  </div>
  <div class="card" style="margin-top:1rem">
    <h2 style="border-bottom:none;margin-top:0">{title}</h2>
    <table style="margin-top:1rem">
      <tbody>{rows_html}</tbody>
    </table>
  </div>
  <div class="footer">Built at {build_time} | CC 产物管理中心</div>
</div>
</body>
</html>'''


# ═══════════════════════════════════════════
# Phase 3b: 详情页（每篇 MD）
# ═══════════════════════════════════════════


def _detail_breadcrumb(rel_path):
    parts = Path(rel_path).parts
    crumbs = ['<a href="/' + "index.html" + '">Dashboard</a>']
    for i, part in enumerate(parts):
        if i == len(parts) - 1:
            crumbs.append(f"<strong>{part}</strong>")
        else:
            # 往上回溯的相对路径
            depth = len(parts) - i - 1
            href = "../" * depth + "index.html"
            crumbs.append(f'<a href="{href}">{part}</a>')
    return '<span class="sep"> / </span>'.join(crumbs)


def render_detail_page(doc, similar, build_time, docs_by_path):
    """渲染单个文档的详情页。"""
    rel = doc["rel_path"]
    depth = len(Path(rel).parts) - 1
    root_prefix = "../" * depth

    # Breadcrumb
    bc = _detail_breadcrumb(rel)

    # Meta
    cat = doc["category"] or "root"
    col = _cat_color(cat)
    date_str = _format_datetime(doc["mtime"])
    tags_h = _tags_html(doc["tags"])
    meta_html = f"""<div class="detail-meta">
  <span class="cat-pill" style="background:{col}">{cat}</span>
  <span>{date_str}</span>
  <span>{doc["word_count"]} words</span>
  {tags_h}
</div>"""

    # TOC sidebar
    toc_html = ""
    if len(doc["headings"]) >= 3:
        toc_items = []
        for level, text in doc["headings"]:
            slug = slugify(text)
            css_class = f"toc-h{level}" if level >= 3 else ""
            toc_items.append(f'<li><a class="{css_class}" href="#{slug}">{text}</a></li>')
        toc_html = f"""<nav class="detail-toc">
  <div style="font-weight:700;font-size:0.85em;color:var(--text-secondary);margin-bottom:0.5rem;padding:0 8px">TABLE OF CONTENTS</div>
  <ul class="toc">{"".join(toc_items)}</ul>
</nav>"""

    # Main content
    body_html = md_to_html(doc["body"], add_heading_ids=True)

    # Related docs
    related_html = ""
    sim_list = similar.get(rel, [])
    if sim_list:
        cards = []
        for other_rel, score in sim_list[:5]:
            other = docs_by_path.get(other_rel)
            if not other:
                continue
            other_href = root_prefix + _html_path(other_rel)
            desc = (other["description"][:80] + "...") if len(other["description"]) > 80 else other["description"]
            other_tags = _tags_html(other.get("tags", []), small=True)
            cards.append(f'''<div class="related-card">
  <a class="related-card-title" href="{other_href}">{other["title"]}</a>
  <div class="related-card-desc">{desc}</div>
  <div style="margin-top:4px">{other_tags}</div>
</div>''')
        if cards:
            related_html = f"""<div class="related-docs">
  <div class="module-title">相关文档</div>
  <div class="related-grid">{"".join(cards)}</div>
</div>"""

    # Scroll spy JS
    scroll_spy_js = """<script>
(function(){
  var observer = new IntersectionObserver(function(entries){
    entries.forEach(function(e){
      if(e.isIntersecting){
        document.querySelectorAll('.toc a').forEach(function(a){a.classList.remove('active')});
        var sel = document.querySelector('.toc a[href="#'+e.target.id+'"]');
        if(sel) sel.classList.add('active');
      }
    });
  },{rootMargin:'-80px 0px -80% 0px'});
  document.querySelectorAll('h1[id],h2[id],h3[id],h4[id]').forEach(function(h){observer.observe(h)});
})();
</script>"""

    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{doc["title"]} - Tianli's Knowledge Dashboard</title>
{SHARED_CSS}
</head>
<body>
<div class="site-header">
  <a href="{root_prefix}index.html" style="font-weight:700;font-size:1.1rem">Tianli's Knowledge Dashboard</a>
</div>
<div class="breadcrumb">{bc}</div>
<div class="container">
  {meta_html}
  <div class="detail-layout">
    {toc_html}
    <div class="detail-main">
      {body_html}
      {related_html}
    </div>
  </div>
  <div class="footer">Built at {build_time} | Three-Phase Knowledge Dashboard</div>
</div>
{scroll_spy_js}
</body>
</html>'''
    return page


# ═══════════════════════════════════════════
# Phase 3c: 知识图谱 (graph.html)
# ═══════════════════════════════════════════


def render_graph_page(docs, edges, stats, build_time):
    """渲染知识图谱页面。"""
    # 构建节点数据
    nodes = []
    for d in docs:
        nodes.append(
            {
                "id": d["rel_path"],
                "title": d["title"],
                "category": d["category"] or "root",
                "word_count": d["word_count"],
                "tags": d["tags"][:5] if d["tags"] else [],
                "description": d["description"][:100],
                "url": _html_path(d["rel_path"]),
            }
        )
    links = []
    for src, tgt, sim in edges:
        links.append({"source": src, "target": tgt, "similarity": round(sim, 3)})

    graph_data = {"nodes": nodes, "links": links}

    # 分类图例
    all_cats = sorted(set(d["category"] or "root" for d in docs))
    legend_items = []
    checkboxes = []
    for cat in all_cats:
        col = _cat_color(cat)
        legend_items.append(
            f'<div style="display:flex;align-items:center;gap:6px;margin-bottom:4px">'
            f'<span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{col}"></span>'
            f'<span style="font-size:0.85em">{cat}</span></div>'
        )
        checkboxes.append(
            f'<label style="display:flex;align-items:center;gap:6px;font-size:0.85em;cursor:pointer">'
            f'<input type="checkbox" checked data-cat="{cat}"> {cat}</label>'
        )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Knowledge Graph - Tianli's Knowledge Dashboard</title>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;overflow:hidden;background:#0f172a;color:#e2e8f0}}
#graph-container{{width:100vw;height:100vh;position:relative}}
svg{{width:100%;height:100%}}
.sidebar{{position:absolute;top:0;left:0;width:240px;height:100vh;background:rgba(15,23,42,0.95);
  border-right:1px solid #334155;padding:1.25rem;overflow-y:auto;display:flex;flex-direction:column;gap:1rem}}
.sidebar h2{{font-size:1rem;color:#f1f5f9}}
.sidebar a{{color:#93c5fd;text-decoration:none;font-size:0.9em}}
.sidebar a:hover{{color:#fff}}
.filter-group{{display:flex;flex-direction:column;gap:4px}}
.tooltip{{position:absolute;background:#1e293b;color:#e2e8f0;padding:10px 14px;border-radius:8px;
  font-size:0.82em;pointer-events:none;box-shadow:0 4px 12px rgba(0,0,0,.4);max-width:260px;
  border:1px solid #334155;opacity:0;transition:opacity .15s}}
.tooltip .tt-title{{font-weight:700;margin-bottom:4px}}
.tooltip .tt-tags{{color:#94a3b8;font-size:0.9em}}
.tooltip .tt-desc{{color:#94a3b8;margin-top:4px;font-size:0.9em}}
</style>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
</head>
<body>
<div id="graph-container">
  <svg id="graph-svg"></svg>
  <div class="sidebar">
    <a href="index.html">&larr; Dashboard</a>
    <h2>Knowledge Graph</h2>
    <div>
      <div style="font-size:0.8em;color:#94a3b8;margin-bottom:6px">FILTER BY CATEGORY</div>
      <div class="filter-group">
        {"".join(checkboxes)}
      </div>
    </div>
    <div>
      <div style="font-size:0.8em;color:#94a3b8;margin-bottom:6px">LEGEND</div>
      {"".join(legend_items)}
    </div>
    <div style="font-size:0.75em;color:#64748b;margin-top:auto">
      {stats["total_docs"]} nodes &middot; {len(edges)} edges
    </div>
  </div>
  <div class="tooltip" id="tooltip"></div>
</div>
<script>
const CATEGORY_COLORS = {json.dumps({cat: _cat_color(cat) for cat in all_cats})};
const graphData = {json.dumps(graph_data)};

const width = window.innerWidth;
const height = window.innerHeight;
const svg = d3.select('#graph-svg');
const g = svg.append('g');
const tooltip = document.getElementById('tooltip');

// Zoom
svg.call(d3.zoom().scaleExtent([0.2, 5]).on('zoom', function(event) {{
  g.attr('transform', event.transform);
}}));

let currentNodes = [...graphData.nodes];
let currentLinks = [...graphData.links];

const simulation = d3.forceSimulation(currentNodes)
  .force('link', d3.forceLink(currentLinks).id(function(d){{return d.id}}).distance(80))
  .force('charge', d3.forceManyBody().strength(-30))
  .force('center', d3.forceCenter(width/2, height/2))
  .force('collide', d3.forceCollide(12));

let linkGroup = g.append('g').attr('class','links');
let nodeGroup = g.append('g').attr('class','nodes');

function render() {{
  linkGroup.selectAll('line').remove();
  nodeGroup.selectAll('circle').remove();

  var linkSel = linkGroup.selectAll('line').data(currentLinks).enter().append('line')
    .attr('stroke','#334155').attr('stroke-opacity',0.6)
    .attr('stroke-width', function(d){{return d.similarity * 3}});

  var nodeSel = nodeGroup.selectAll('circle').data(currentNodes).enter().append('circle')
    .attr('r', function(d){{return Math.max(4, Math.log2(d.word_count||1)*2)}})
    .attr('fill', function(d){{return CATEGORY_COLORS[d.category]||'#64748b'}})
    .attr('stroke','#0f172a').attr('stroke-width',1).attr('cursor','pointer')
    .call(d3.drag()
      .on('start',function(event,d){{if(!event.active)simulation.alphaTarget(0.3).restart();d.fx=d.x;d.fy=d.y}})
      .on('drag',function(event,d){{d.fx=event.x;d.fy=event.y}})
      .on('end',function(event,d){{if(!event.active)simulation.alphaTarget(0);d.fx=null;d.fy=null}})
    );

  nodeSel.on('click',function(event,d){{window.location=d.url}});
  nodeSel.on('mouseover',function(event,d){{
    var tags = d.tags && d.tags.length ? '<div class="tt-tags">'+d.tags.join(', ')+'</div>' : '';
    var desc = d.description ? '<div class="tt-desc">'+d.description+'</div>' : '';
    tooltip.innerHTML='<div class="tt-title">'+d.title+'</div>'+tags+desc;
    tooltip.style.opacity='1';
    tooltip.style.left=(event.pageX+12)+'px';
    tooltip.style.top=(event.pageY-12)+'px';
  }});
  nodeSel.on('mousemove',function(event){{
    tooltip.style.left=(event.pageX+12)+'px';
    tooltip.style.top=(event.pageY-12)+'px';
  }});
  nodeSel.on('mouseout',function(){{tooltip.style.opacity='0'}});

  simulation.nodes(currentNodes);
  simulation.force('link').links(currentLinks);
  simulation.alpha(0.8).restart();

  simulation.on('tick',function(){{
    linkSel.attr('x1',function(d){{return d.source.x}}).attr('y1',function(d){{return d.source.y}})
      .attr('x2',function(d){{return d.target.x}}).attr('y2',function(d){{return d.target.y}});
    nodeSel.attr('cx',function(d){{return d.x}}).attr('cy',function(d){{return d.y}});
  }});
}}

render();

// Filter
document.querySelectorAll('[data-cat]').forEach(function(cb){{
  cb.addEventListener('change',function(){{
    var activeCats = new Set();
    document.querySelectorAll('[data-cat]:checked').forEach(function(c){{activeCats.add(c.getAttribute('data-cat'))}});
    currentNodes = graphData.nodes.filter(function(n){{return activeCats.has(n.category)}});
    var nodeIds = new Set(currentNodes.map(function(n){{return n.id}}));
    currentLinks = graphData.links.filter(function(l){{
      var s = typeof l.source === 'object' ? l.source.id : l.source;
      var t = typeof l.target === 'object' ? l.target.id : l.target;
      return nodeIds.has(s) && nodeIds.has(t);
    }});
    // Reset link references to use IDs for re-binding
    currentLinks = currentLinks.map(function(l){{
      return {{source: typeof l.source === 'object' ? l.source.id : l.source,
               target: typeof l.target === 'object' ? l.target.id : l.target,
               similarity: l.similarity}};
    }});
    render();
  }});
}});
</script>
</body>
</html>"""

    return page, graph_data


# ═══════════════════════════════════════════
# Phase 3d: 目录索引
# ═══════════════════════════════════════════


def render_directory_index(dir_rel, files_in_dir, subdirs, docs_by_path, build_time):
    """为目录生成 index.html。"""
    is_root = dir_rel == "."
    dir_name = Path(dir_rel).name if not is_root else "Home"
    depth = 0 if is_root else len(Path(dir_rel).parts)
    root_prefix = "../" * depth

    # Breadcrumb
    bc_html = ""
    if not is_root:
        parts = Path(dir_rel).parts
        crumbs = [f'<a href="{root_prefix}index.html">Dashboard</a>']
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                crumbs.append(f"<strong>{part}</strong>")
            else:
                up = "../" * (len(parts) - i - 1)
                crumbs.append(f'<a href="{up}index.html">{part}</a>')
        bc_html = f'<div class="breadcrumb">{"<span class=sep> / </span>".join(crumbs)}</div>'

    sections = []

    # 子目录
    if subdirs:
        items = []
        for d in sorted(subdirs):
            items.append(f'<li><span style="margin-right:6px">\U0001f4c1</span><a href="{d}/index.html">{d}</a></li>')
        sections.append(f'<div class="dir-section-title">Directories</div><ul class="dir-list">{"".join(items)}</ul>')

    # 文件列表（按 mtime 倒序）
    if files_in_dir:
        sorted_files = sorted(files_in_dir, key=lambda d: -d["mtime"])
        items = []
        for d in sorted_files:
            fname_html = Path(d["rel_path"]).with_suffix(".html").name
            desc = (d["description"][:80] + "...") if len(d["description"]) > 80 else d["description"]
            tags_h = _tags_html(d.get("tags", []), small=True)
            date_str = _format_date(d["mtime"])
            items.append(f'''<li><div class="file-item">
  <div class="file-info">
    <a class="file-title" href="{fname_html}">{d["title"]}</a>
    <div class="file-desc">{desc}</div>
    <div class="file-meta">{tags_h}</div>
  </div>
  <span class="file-date">{date_str}</span>
</div></li>''')
        sections.append(
            f'<div class="dir-section-title">Files ({len(files_in_dir)})</div><ul class="file-list">{"".join(items)}</ul>'
        )

    if not sections:
        sections.append('<p style="color:var(--text-secondary)">Empty directory</p>')

    content = "\n".join(sections)

    page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{dir_name} - Tianli's Knowledge Dashboard</title>
{SHARED_CSS}
</head>
<body>
<div class="site-header">
  <a href="{root_prefix}index.html" style="font-weight:700;font-size:1.1rem">Tianli's Knowledge Dashboard</a>
  <a href="{root_prefix}index.html" style="font-size:0.85em">&larr; Dashboard</a>
</div>
{bc_html}
<div class="container">
  <h1>{dir_name}</h1>
  {content}
  <div class="footer">Built at {build_time} | Three-Phase Knowledge Dashboard</div>
</div>
</body>
</html>'''
    return page


# ═══════════════════════════════════════════
# 主构建逻辑
# ═══════════════════════════════════════════


def build_site(src_dir, output_dir, cc_dir=None):
    """三阶段管线主构建函数。"""
    src = Path(src_dir).resolve()
    out = Path(output_dir).resolve()

    # 清空输出目录
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    build_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ──────── Phase 1: COLLECT ────────
    print("Phase 1/3: Collecting documents...")
    docs = collect_all_docs(src)
    print(f"  Collected {len(docs)} documents")

    # CC 产物收集
    cc_memories = []
    cc_sessions = []
    duplicates = []
    if cc_dir:
        print(f"  Collecting CC artifacts from {cc_dir}...")
        cc_memories = collect_cc_memory(cc_dir)
        print(f"  CC memories: {len(cc_memories)} files")
        cc_sessions = collect_cc_sessions(cc_dir)
        print(f"  CC sessions: {len(cc_sessions)} entries")
        duplicates = detect_duplicates(docs, cc_memories)
        if duplicates:
            print(f"  Duplicates detected: {len(duplicates)} pairs")

    projects = collect_project_status(cc_memories)

    # 按 rel_path 索引
    docs_by_path = {d["rel_path"]: d for d in docs}

    # ──────── Phase 2: ENRICH ────────
    print("Phase 2/3: Enriching (keywords, similarity)...")
    keywords = compute_tfidf(docs)

    # 平均关键词数
    avg_kw = sum(len(v) for v in keywords.values()) / max(len(keywords), 1)
    print(f"  Keywords extracted: {len(keywords)} docs, avg {avg_kw:.1f} per doc")

    similar, edges = compute_similarity(docs, keywords)
    print(f"  Similarity computed: {len(edges)} edges")

    stats = compute_stats(docs)

    # ──────── Phase 3: RENDER ────────
    print("Phase 3/3: Rendering...")

    # 3a. Dashboard
    dashboard_html = render_dashboard(
        docs,
        projects,
        stats,
        similar,
        build_time,
        cc_memories=cc_memories,
        cc_sessions=cc_sessions,
        duplicates=duplicates,
    )
    (out / "index.html").write_text(dashboard_html, encoding="utf-8")
    print("  Dashboard: index.html")

    # 3b. Detail pages（跳过根 index.md，避免覆盖 Dashboard）
    detail_count = 0
    for doc in docs:
        html_rel = _html_path(doc["rel_path"])
        if html_rel == "index.html":
            continue  # 根 index.md 不覆盖 Dashboard
        page_html = render_detail_page(doc, similar, build_time, docs_by_path)
        out_path = out / html_rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")
        detail_count += 1
    print(f"  Detail pages: {detail_count}")

    # 3b+. CC Memory detail pages
    cc_mem_count = 0
    for mem in cc_memories:
        page_html = render_cc_memory_detail(mem, build_time)
        out_path = out / mem["html_rel"]
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")
        cc_mem_count += 1
    if cc_mem_count:
        print(f"  CC Memory pages: {cc_mem_count}")

    # 3b+. CC Session detail pages (skip trivial)
    cc_ses_count = 0
    for s in cc_sessions:
        sid = s.get("session_id", "")
        if not sid or s.get("trivial"):
            continue
        page_html = render_cc_session_detail(s, build_time)
        out_path = out / "cc-sessions" / f"{sid}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_html, encoding="utf-8")
        cc_ses_count += 1
    if cc_ses_count:
        print(f"  CC Session pages: {cc_ses_count}")

    # 3c. Knowledge graph
    graph_html, graph_data = render_graph_page(docs, edges, stats, build_time)
    (out / "graph.html").write_text(graph_html, encoding="utf-8")
    (out / "graph_data.json").write_text(json.dumps(graph_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  Knowledge graph: graph.html + graph_data.json")

    # 3d. Directory indexes
    # 收集目录结构
    dir_files = defaultdict(list)  # dir_rel -> [doc_dicts]
    dir_subdirs = defaultdict(set)  # dir_rel -> {subdir_names}

    for doc in docs:
        rel = Path(doc["rel_path"])
        parent = str(rel.parent)
        if parent == ".":
            parent = "."
        dir_files[parent].append(doc)

        # 注册所有父目录链
        current = rel.parent
        while str(current) != ".":
            grandparent = str(current.parent) if str(current.parent) != "." else "."
            dir_subdirs[grandparent].add(current.name)
            current = current.parent

    # 确保根目录存在
    if "." not in dir_files and "." not in dir_subdirs:
        dir_files["."] = []
    # 收集顶级子目录名
    for d in set(dir_files.keys()).union(set(dir_subdirs.keys())):
        p = Path(d)
        if d != "." and str(p.parent) == ".":
            dir_subdirs["."].add(p.name)

    all_dirs = set(dir_files.keys()).union(set(dir_subdirs.keys()))
    dir_count = 0
    for d in all_dirs:
        idx_html = render_directory_index(d, dir_files.get(d, []), dir_subdirs.get(d, set()), docs_by_path, build_time)
        idx_path = out / (d if d != "." else "") / "index.html"
        # 不覆盖根 index.html（那是 dashboard）
        if d == ".":
            continue
        idx_path.parent.mkdir(parents=True, exist_ok=True)
        idx_path.write_text(idx_html, encoding="utf-8")
        dir_count += 1
    print(f"  Directory indexes: {dir_count}")

    total_files = 1 + detail_count + dir_count + 2  # dashboard + details + dirs + graph.html + graph_data.json
    print(f"\nDone! Built {total_files} files to {out}")


# ═══════════════════════════════════════════
# 入口
# ═══════════════════════════════════════════


def main():
    # 解析 --cc-dir 参数
    args = sys.argv[1:]
    cc_dir = None
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == "--cc-dir" and i + 1 < len(args):
            cc_dir = args[i + 1]
            i += 2
        else:
            filtered.append(args[i])
            i += 1

    if not filtered:
        print("Usage: python3 build_site.py <source_dir> [output_dir] [--cc-dir <path>]")
        print("  source_dir: Directory with .md files (e.g., ~/docs)")
        print("  output_dir: Where to write HTML (default: <source_dir>/_site)")
        print("  --cc-dir:   Path to .claude config directory for CC artifacts")
        sys.exit(1)

    src_dir = filtered[0]
    output_dir = filtered[1] if len(filtered) > 1 else os.path.join(src_dir, "_site")

    build_site(src_dir, output_dir, cc_dir=cc_dir)


if __name__ == "__main__":
    main()
