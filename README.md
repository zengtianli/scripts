# Scripts

![macOS](https://img.shields.io/badge/platform-macOS-lightgrey?style=for-the-badge) ![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge) ![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge) ![Raycast](https://img.shields.io/badge/Raycast-integrated-orange?style=for-the-badge)

---

**English** | [中文](#中文)

A collection of 50+ macOS utility scripts for document processing, data conversion, file management, system automation, and hydraulic engineering. Integrated with [Raycast](https://raycast.com/) for quick access.

## Quick Start

```bash
git clone https://github.com/zengtianli/scripts.git
cd scripts
pip3 install -r requirements.txt
python3 lib/tools/health_check.py   # verify everything works
```

### Raycast Integration

1. Open Raycast Settings (Cmd + ,)
2. Go to Extensions > Script Commands
3. Add script directory: `<your-path>/scripts/raycast/commands`
4. Refresh — commands ready to use

### Environment Variables

Copy `.env.example` and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required By | Description |
|----------|-------------|-------------|
| `TIANYANCHA_API_TOKEN` | company_query | Tianyancha API token |
| `AMAP_API_KEY` | geocode | Amap (Gaode) Maps API key |

## Document Processing (`scripts/document/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `md_tools.py` | Markdown toolkit: format, merge, split, strip blockquotes, convert to docx/HTML | `python3 md_tools.py format doc.md` / `python3 md_tools.py merge *.md -o out.md` / `python3 md_tools.py split-heading doc.md` / `python3 md_tools.py to-docx doc.md` |
| `md_docx_template.py` | Markdown to styled DOCX using reference template | `python3 md_docx_template.py input.md -t template.docx -o output.docx` |
| `docx_text_formatter.py` | Auto-fix Chinese quotes, punctuation, unit symbols | `python3 docx_text_formatter.py report.docx` (Raycast: select file and run) |
| `docx_extract.py` | Extract text from .docx as Markdown | `python3 docx_extract.py report.docx` / `python3 docx_extract.py report.docx --split-chapter` |
| `docx_apply_template.py` | Apply template styling to target docx | `python3 docx_apply_template.py input.docx -t template.docx -o output.docx` |
| `docx_apply_image_caption.py` | Auto-style image captions (ZDWP format) | `python3 docx_apply_image_caption.py report.docx` |
| `docx_format_check.py` | Two-layer format validation (ZIP integrity + semantic comparison) | `python3 docx_format_check.py target.docx --reference ref.docx` |
| `docx_style_cleanup.py` | Clean up / rename / merge unused Word styles | `python3 docx_style_cleanup.py report.docx --preview` / `python3 docx_style_cleanup.py report.docx --cleanup` |
| `docx_track_changes.py` | Read/write Word track changes and revision marks | `python3 docx_track_changes.py read report.docx` / `python3 docx_track_changes.py apply report.docx rules.json` |
| `docx_to_md.sh` | Convert DOCX to Markdown via pandoc/markitdown | `./docx_to_md.sh report.docx` |
| `pptx_tools.py` | PPT standardization: font, text format, table style | `python3 pptx_tools.py font-yahei deck.pptx` / `python3 pptx_tools.py all deck.pptx` |
| `pptx_to_md.py` | Convert PowerPoint to Markdown | `python3 pptx_to_md.py presentation.pptx` |
| `report_quality_check.py` | Quality check: forbidden words, bullet points, duplicates | `python3 report_quality_check.py report.md` / `python3 report_quality_check.py report.md --fix` |
| `scan_sensitive_words.py` | AI-powered sensitive word detection for bid documents | `python3 scan_sensitive_words.py bid_doc.md` |
| `bid_standardize.py` | Standardize Markdown structure for bidding documents | `python3 bid_standardize.py bid.md --fix` |
| `bullet_to_paragraph.py` | Convert bullet lists to formal document paragraphs (AI) | `python3 bullet_to_paragraph.py notes.md -o output.md` |
| `table_tools.py` | Table name/intro standardization | `python3 table_tools.py check report.docx` / `python3 table_tools.py reorder report.docx` |
| `chart.py` | Data-driven chart generation (bar, Gantt, flow) from JSON | `python3 chart.py config.json` / `python3 chart.py --type gantt config.json` |
| `chart_insert.py` | Replace ASCII art code blocks with PNG images | `python3 chart_insert.py check doc.md` / `python3 chart_insert.py fix doc.md` |
| `frontmatter_gen.py` | Batch generate YAML frontmatter for Markdown files (AI) | `python3 frontmatter_gen.py docs/` |

## Data Conversion (`scripts/data/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `convert.py` | Unified format conversion: CSV, TXT, XLSX, XLS | `python3 convert.py to-csv input.xlsx` / `python3 convert.py to-xlsx input.csv` / `python3 convert.py to-txt input.xlsx` |
| `xlsx_lowercase.py` | Convert English text to lowercase in Excel/Word | `python3 xlsx_lowercase.py data.xlsx` |
| `xlsx_merge_tables.py` | AI-based name matching and field mapping for table merge | `python3 xlsx_merge_tables.py main.xlsx lookup.xlsx -o merged.xlsx` |
| `xlsx_splitsheets.py` | Split Excel file into one file per worksheet | `python3 xlsx_splitsheets.py workbook.xlsx` |
| `xlsx_encode_duplicates.py` | Generate unique codes for duplicate enterprise entries | `python3 xlsx_encode_duplicates.py enterprises.xlsx` |

## File Management (`scripts/file/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `downloads_organizer.py` | Auto-organize Downloads by file type | `python3 downloads_organizer.py ~/Downloads` (config: `downloads_organizer.yaml`) |
| `smart_rename.py` | AI-driven intelligent file renaming | `python3 smart_rename.py analyze ~/Downloads/docs` / `python3 smart_rename.py execute ~/Downloads/docs` |
| `file_copy.py` | Copy file path or contents to clipboard | `python3 file_copy.py` (operates on Finder selection) |
| `file_print.py` | Print selected files (PDF, images, text) | `python3 file_print.py` (operates on Finder selection) |
| `file_run.py` | Execute selected shell/Python scripts | `python3 file_run.py` (operates on Finder selection) |
| `folder_paste.sh` | Paste clipboard files to Finder current directory | `./folder_paste.sh` |
| `folder_add_prefix.py` | Add prefix to all files in a folder | `python3 folder_add_prefix.py ~/docs --prefix "2026-"` |
| `folder_create.py` | Create new folder via Finder interaction | `python3 folder_create.py` |
| `folder_move_up_remove.py` | Move files up one level, remove empty parent | `python3 folder_move_up_remove.py ~/docs/subdir` |
| `project_sort.py` | Organize files into subdirectories by project prefix | `python3 project_sort.py ~/Downloads` |
| `scan_binary_manifest.py` | Generate file manifests for binary-heavy directories | `python3 scan_binary_manifest.py ~/Work/project` |

## System Automation (`scripts/system/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `sys_app_launcher.py` | List running apps and launch essential apps | `python3 sys_app_launcher.py` (reads `~/Desktop/essential_apps.txt`) |
| `display_1080.sh` | Switch external display to 1080p (for presentations) | `./display_1080.sh` |
| `display_4k.sh` | Switch external display to 4K resolution | `./display_4k.sh` |
| `create_reminder.sh` | Create macOS Reminder via AppleScript | `./create_reminder.sh "Buy milk" "2026-04-03 18:00" "Shopping"` |
| `dingtalk_gov.sh` | Launch DingTalk Government app | `./dingtalk_gov.sh` |

## Network Proxy (`scripts/network/`)

ClashX Pro management via Raycast quick commands.

| Script | Description | Usage |
|--------|-------------|-------|
| `clashx_enhanced.sh` | Toggle TUN enhanced mode | Raycast: "ClashX Enhanced" |
| `clashx_mode_rule.sh` | Switch to Rule mode | Raycast: "ClashX Rule" |
| `clashx_mode_global.sh` | Switch to Global mode | Raycast: "ClashX Global" |
| `clashx_mode_direct.sh` | Switch to Direct mode | Raycast: "ClashX Direct" |
| `clashx_status.sh` | Show current proxy status | Raycast: "ClashX Status" |
| `clashx_proxy.sh` | Toggle system proxy on/off | Raycast: "ClashX Proxy" |

## Developer Tools (`scripts/tools/`)

| Script | Description | Usage |
|--------|-------------|-------|
| `llm_client.py` | Unified LLM calling module (haiku/sonnet/opus) | `from tools.llm_client import chat; chat("system prompt", "message")` |
| `cc_sessions.py` | CC session index + export toolkit | `python3 cc_sessions.py index --summarize` / `python3 cc_sessions.py export --date-from 2026-03-01` |
| `git_smart_push.py` | Batch commit + push repos with AI commit messages | `python3 git_smart_push.py` (reads repo-map.json) |
| `git_auto_stage.sh` | PostToolUse hook: auto-stage modified files | Used as Claude Code hook |
| `memory_sync.sh` | PostToolUse hook: sync memory to ~/docs/ | Used as Claude Code hook |
| `tts_volcano.py` | Text-to-speech via Volcano Engine | `python3 tts_volcano.py "你好世界" -o hello.mp3` |
| `app_open.py` | Open Finder selection in terminal or app | `python3 app_open.py` (operates on Finder selection) |
| `prepare_share.sh` | Package project for sharing (dereference symlinks) | `./prepare_share.sh ~/Dev/myproject` |
| `dereference_links.py` | Replace symlinks with actual files | `python3 dereference_links.py ~/Dev/myproject` |
| `printer/` | Canon iR C3322L printer diagnostics and repair | `./printer/scripts/diagnose.sh` / `./printer/scripts/fix.sh` |

## Repo Management (`repo_manager.py`)

Unified tool for GitHub repository promotion, auditing, and screenshots.

```bash
python3 repo_manager.py promote [--repos repo1,repo2]    # batch GitHub metadata update
python3 repo_manager.py audit [project1 project2]        # audit README, gitignore, deps
python3 repo_manager.py screenshot streamlit <name> <url> # capture app screenshots
```

## Shared Libraries (`lib/`)

| Module | Description |
|--------|-------------|
| `clipboard.py` | Clipboard read/write (macOS pbcopy/pbpaste) |
| `display.py` | Console output formatting (success/error/warning/info) |
| `file_ops.py` | File extension checking, existence validation |
| `finder.py` | macOS Finder interaction via AppleScript |
| `progress.py` | Progress tracking with success/failure/skip counts |
| `usage_log.py` | Script usage statistics to CSV log |
| `env.py` | Environment config, path detection, Raycast env loading |
| `docx_xml.py` | Word XML namespace constants |
| `clashx.sh` | ClashX Pro API helper functions |
| `common.sh` | Raycast shell script common library |
| `hydraulic/` | Water engineering domain library (encoding, QGIS, Streamlit utils) |

### Maintenance Tools (`lib/tools/`)

| Tool | Description | Usage |
|------|-------------|-------|
| `health_check.py` | Validate project integrity (broken links, imports) | `python3 lib/tools/health_check.py` |
| `cf_api.py` | Cloudflare DNS/Access API CLI | `python3 lib/tools/cf_api.py dns list` |
| `gen_claude_md.py` | Batch generate CLAUDE.md for projects (AI) | `python3 lib/tools/gen_claude_md.py` |
| `sync_index.py` | Scan scripts and generate index | `python3 lib/tools/sync_index.py` |
| `vps_cmd.py` | SSH wrapper for VPS operations | `python3 lib/tools/vps_cmd.py status` |
| `validate_raycast_commands.py` | Validate Raycast command metadata | `python3 lib/tools/validate_raycast_commands.py` |

## Projects (`projects/`)

| Project | Type | Description | Usage |
|---------|------|-------------|-------|
| `company_query` | CLI | Company info query via Tianyancha API | `python3 projects/company_query/company_industry_query.py companies.xlsx` |

## Project Structure

```
scripts/
├── scripts/               # Utility scripts by category
│   ├── data/              # Data conversion (xlsx, csv, txt)
│   ├── document/          # Document processing (docx, md, pptx)
│   ├── file/              # File operations
│   ├── system/            # System tools
│   ├── network/           # Network proxy (ClashX)
│   └── tools/             # Dev tools (Git, LLM, TTS, CC sessions)
├── lib/                   # Shared libraries
│   ├── hydraulic/         # Water engineering domain
│   └── tools/             # Maintenance tools (health check, CF API)
├── projects/              # Multi-file projects
│   └── company_query/     # Tianyancha enterprise query
├── raycast/               # Raycast script commands
│   ├── commands/          # Shell wrappers with @raycast metadata
│   └── lib/               # Shared runner scripts
├── templates/             # Document templates (gitignored)
├── repo_manager.py        # GitHub repo management (promote/audit/screenshot)
└── docs/                  # Documentation
```

## Related

- [dockit](https://github.com/zengtianli/dockit) — Document processing toolkit

## License

MIT

---

<a id="中文"></a>

# Scripts（中文）

macOS 个人效率工具脚本库，包含 50+ 个功能脚本，覆盖文档处理、数据转换、文件管理、系统自动化和水利工程等领域。通过 [Raycast](https://raycast.com/) 集成快捷命令。

详细使用案例见上方英文文档，每个脚本均包含命令示例。

## 快速开始

```bash
git clone https://github.com/zengtianli/scripts.git
cd scripts
pip3 install -r requirements.txt
python3 lib/tools/health_check.py
```

### Raycast 集成

1. 打开 Raycast 设置（Cmd + ,）
2. 进入 Extensions > Script Commands
3. 添加脚本目录：`<你的路径>/scripts/raycast/commands`
4. 刷新即可使用

### 环境变量

```bash
cp .env.example .env
```

| 变量 | 用于 | 说明 |
|------|------|------|
| `TIANYANCHA_API_TOKEN` | company_query | 天眼查 API Token |
| `AMAP_API_KEY` | geocode | 高德地图 API Key |

## 许可证

MIT
