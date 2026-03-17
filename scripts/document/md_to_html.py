#!/usr/bin/env python3
"""md_to_html.py — 把 MD 文件渲染成好看的 HTML 页面，在浏览器中打开

用法：
    python3 md_to_html.py file.md              # 单个文件
    python3 md_to_html.py dir/                  # 整个目录（生成带导航的索引页）
    python3 md_to_html.py file1.md file2.md     # 多个文件
"""

import sys
import os
import re
import webbrowser
import tempfile
from pathlib import Path

# 内联 CSS，不依赖外部文件
CSS = """
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    line-height: 1.6; color: #1f2937; background: #f9fafb;
    max-width: 900px; margin: 0 auto; padding: 2rem;
  }
  h1 { font-size: 1.8rem; border-bottom: 2px solid #e5e7eb; padding-bottom: 0.5rem; margin: 1.5rem 0 1rem; color: #111827; }
  h2 { font-size: 1.4rem; border-bottom: 1px solid #e5e7eb; padding-bottom: 0.3rem; margin: 1.3rem 0 0.8rem; color: #1f2937; }
  h3 { font-size: 1.15rem; margin: 1rem 0 0.5rem; color: #374151; }
  p { margin: 0.5rem 0; }
  a { color: #2563eb; text-decoration: none; }
  a:hover { text-decoration: underline; }
  code { background: #f3f4f6; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.9em; }
  pre { background: #1f2937; color: #f9fafb; padding: 1rem; border-radius: 8px; overflow-x: auto; margin: 0.8rem 0; }
  pre code { background: none; padding: 0; color: inherit; }
  blockquote { border-left: 4px solid #3b82f6; padding: 0.5rem 1rem; margin: 0.8rem 0; background: #eff6ff; color: #1e40af; }
  table { border-collapse: collapse; width: 100%; margin: 0.8rem 0; }
  th, td { border: 1px solid #d1d5db; padding: 0.5rem 0.75rem; text-align: left; }
  th { background: #f3f4f6; font-weight: 600; }
  tr:nth-child(even) { background: #f9fafb; }
  ul, ol { padding-left: 1.5rem; margin: 0.5rem 0; }
  li { margin: 0.2rem 0; }
  hr { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0; }
  .nav { background: #1f2937; color: white; padding: 0.8rem 1.5rem; margin: -2rem -2rem 2rem; }
  .nav a { color: #93c5fd; margin-right: 1rem; }
  .file-list { list-style: none; padding: 0; }
  .file-list li { padding: 0.5rem 0; border-bottom: 1px solid #e5e7eb; }
  .file-list .date { color: #6b7280; font-size: 0.85em; margin-left: 0.5rem; }
  .emoji { font-size: 1.1em; }
  input[type="checkbox"] { margin-right: 0.3rem; }
</style>
"""


def md_to_html_simple(md_text):
    """简易 MD → HTML 转换，不依赖第三方库"""
    html = md_text

    # 转义 HTML 特殊字符（但保留已有的 HTML 标签）
    # 先处理代码块
    code_blocks = []
    def save_code(m):
        code_blocks.append(m.group(1))
        return f'__CODE_BLOCK_{len(code_blocks)-1}__'
    html = re.sub(r'```[\w]*\n(.*?)```', save_code, html, flags=re.DOTALL)

    inline_codes = []
    def save_inline(m):
        inline_codes.append(m.group(1))
        return f'__INLINE_CODE_{len(inline_codes)-1}__'
    html = re.sub(r'`([^`]+)`', save_inline, html)

    # 表格
    def convert_table(m):
        lines = m.group(0).strip().split('\n')
        rows = []
        for i, line in enumerate(lines):
            line = line.strip()
            if not line.startswith('|'):
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if i == 1 and all(re.match(r'^[-:]+$', c) for c in cells):
                continue  # separator row
            tag = 'th' if i == 0 else 'td'
            row = ''.join(f'<{tag}>{c}</{tag}>' for c in cells)
            rows.append(f'<tr>{row}</tr>')
        return f'<table>{"".join(rows)}</table>'
    html = re.sub(r'(\|.+\|[\n\r]+)+', convert_table, html)

    # Headers
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)

    # Bold, italic
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'\*(.+?)\*', r'<em>\1</em>', html)

    # Checkbox
    html = re.sub(r'- \[x\]', r'<li><input type="checkbox" checked disabled>', html)
    html = re.sub(r'- \[ \]', r'<li><input type="checkbox" disabled>', html)

    # Lists
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)

    # Blockquote
    html = re.sub(r'^> (.+)$', r'<blockquote>\1</blockquote>', html, flags=re.MULTILINE)

    # HR
    html = re.sub(r'^---+$', r'<hr>', html, flags=re.MULTILINE)

    # Links
    html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)

    # Paragraphs (lines that aren't already HTML)
    lines = html.split('\n')
    result = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('<') and not stripped.startswith('__CODE') and not stripped.startswith('__INLINE'):
            result.append(f'<p>{line}</p>')
        else:
            result.append(line)
    html = '\n'.join(result)

    # Restore code blocks
    for i, block in enumerate(code_blocks):
        html = html.replace(f'__CODE_BLOCK_{i}__', f'<pre><code>{block}</code></pre>')
    for i, code in enumerate(inline_codes):
        html = html.replace(f'__INLINE_CODE_{i}__', f'<code>{code}</code>')

    return html


def render_file(md_path, output_dir=None):
    """渲染单个 MD 文件为 HTML"""
    md_path = Path(md_path)
    md_text = md_path.read_text(encoding='utf-8')

    title = md_path.stem
    # 从第一个 # 标题提取
    title_match = re.search(r'^# (.+)$', md_text, re.MULTILINE)
    if title_match:
        title = title_match.group(1)

    body = md_to_html_simple(md_text)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    {CSS}
</head>
<body>
    <div class="nav">
        <strong>📄 {md_path.name}</strong>
        <span style="float:right;color:#9ca3af;font-size:0.85em">{md_path.parent}</span>
    </div>
    {body}
</body>
</html>"""

    if output_dir:
        out = Path(output_dir) / f"{md_path.stem}.html"
    else:
        out = Path(tempfile.mkdtemp()) / f"{md_path.stem}.html"

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding='utf-8')
    return out


def render_directory(dir_path, output_dir=None):
    """渲染整个目录为带索引的 HTML"""
    dir_path = Path(dir_path)
    md_files = sorted(dir_path.glob('**/*.md'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not md_files:
        print(f"目录 {dir_path} 中没有找到 .md 文件")
        sys.exit(1)

    if output_dir is None:
        output_dir = Path(tempfile.mkdtemp())
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 渲染每个文件
    file_links = []
    for md in md_files:
        out = render_file(md, output_dir)
        rel = md.relative_to(dir_path)
        mtime = os.path.getmtime(md)
        from datetime import datetime
        date_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        file_links.append((rel, out.name, date_str))

    # 生成索引页
    items = '\n'.join(
        f'<li><a href="{name}">{rel}</a><span class="date">{date}</span></li>'
        for rel, name, date in file_links
    )

    index_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{dir_path.name} — 文件浏览</title>
    {CSS}
</head>
<body>
    <div class="nav"><strong>📁 {dir_path}</strong> <span style="color:#9ca3af">({len(md_files)} 个文件)</span></div>
    <h1>{dir_path.name}</h1>
    <ul class="file-list">{items}</ul>
</body>
</html>"""

    index_path = output_dir / 'index.html'
    index_path.write_text(index_html, encoding='utf-8')
    return index_path


def main():
    if len(sys.argv) < 2:
        print("用法: python3 md_to_html.py <file.md|directory/> [file2.md ...]")
        sys.exit(1)

    target = sys.argv[1]

    if os.path.isdir(target):
        out = render_directory(target)
        print(f"✅ 索引页: {out}")
        webbrowser.open(f'file://{out}')
    elif len(sys.argv) > 2:
        # 多个文件
        tmpdir = Path(tempfile.mkdtemp())
        for f in sys.argv[1:]:
            render_file(f, tmpdir)
        out = render_directory_from_files(sys.argv[1:], tmpdir)
        webbrowser.open(f'file://{out}')
    else:
        out = render_file(target)
        print(f"✅ {out}")
        webbrowser.open(f'file://{out}')


if __name__ == '__main__':
    main()
