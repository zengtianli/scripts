# Scripts

![macOS](https://img.shields.io/badge/platform-macOS-lightgrey?style=for-the-badge) ![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge) ![License: MIT](https://img.shields.io/badge/license-MIT-green?style=for-the-badge) ![Raycast](https://img.shields.io/badge/Raycast-integrated-orange?style=for-the-badge)

---

**English** | [中文](#中文)

40 macOS utility scripts for document processing, data conversion, file management, and system automation. Designed for a hydraulic engineering workflow, integrated with [Raycast](https://raycast.com/) for keyboard-driven access.

## Quick Start

```bash
git clone https://github.com/zengtianli/scripts.git
cd scripts
pip3 install -r requirements.txt
python3 lib/tools/health_check.py
```

**Raycast**: Settings → Extensions → Script Commands → add `scripts/raycast/commands`.

**Environment**: copy `.env.example` to `.env` and fill in API keys (`TIANYANCHA_API_TOKEN`, `AMAP_API_KEY`).

---

## Document Processing — `scripts/document/` (13 scripts)

### md_tools.py — Markdown 统一工具

Markdown 文件的格式化、合并、拆分、转换、frontmatter 生成。7 个子命令覆盖日常 Markdown 操作。

**场景**: 写完报告的 Markdown 稿件后，修正标点格式、合并多个章节文件、转成 DOCX 提交。

```bash
python3 md_tools.py format doc.md                   # 修正中文标点、引号、空格
python3 md_tools.py merge ch1.md ch2.md -o book.md  # 合并多个文件
python3 md_tools.py split doc.md                     # 按一级标题拆分
python3 md_tools.py strip docs/                      # 去除 blockquote 标记
python3 md_tools.py to-docx doc.md -o report.docx   # 转 Word
python3 md_tools.py to-html doc.md                   # 渲染 HTML 并打开
python3 md_tools.py frontmatter docs/ --dry-run      # AI 生成 YAML frontmatter
```

### md_docx_template.py — Markdown 转带样式 DOCX

从参考模板中提取标题/正文样式，然后将 Markdown 转为排版完整的 Word 文档。

**场景**: 用 Markdown 写报告，但最终交付要求套甲方的 Word 模板样式。

```bash
python3 md_docx_template.py extract template.docx            # 提取样式
python3 md_docx_template.py convert report.md -o report.docx # 带样式转换
python3 md_docx_template.py report.md -t template.docx -o report.docx  # 一步到位
```

### docx_text_formatter.py — Word 文本格式自动修正

自动修正 Word 文档中的标点和格式问题：英文引号→中文引号、英文标点→中文标点、单位符号上标（m2→m²）。

**场景**: 同事给的 Word 稿件标点混乱，需要批量修正后交付。

```bash
python3 docx_text_formatter.py report.docx           # 修正单个文件
python3 docx_text_formatter.py *.docx                # 批量修正
```

### docx_apply_template.py — 套模板样式 + 样式清理

两个功能：将模板的样式注入到目标文档（apply），或清理文档中冗余/未使用的样式（cleanup）。

**场景**: 报告写好了但样式是默认的，需要套上公司模板；或文档经过多次编辑样式定义杂乱需要清理。

```bash
python3 docx_apply_template.py apply input.docx -t template.docx -o output.docx
python3 docx_apply_template.py cleanup input.docx --preview   # 预览要清理的样式
python3 docx_apply_template.py cleanup input.docx -o clean.docx
```

### docx_apply_image_caption.py — 图片题注样式

自动识别 Word 文档中的图片段落和题注，应用 ZDWP 标准图名样式（居中、间距）。

**场景**: 水利报告中大量图片需要统一题注格式。

```bash
python3 docx_apply_image_caption.py report.docx
python3 docx_apply_image_caption.py *.docx           # 批量处理
```

### docx_tools.py — DOCX 检查提取工具集

三合一：提取文本（extract）、格式校验（check）、修订标记管理（track-changes）。

**场景**: 需要从 Word 提取纯文本做分析；或对比两个版本的格式差异；或读取审阅意见。

```bash
# 提取文本
python3 docx_tools.py extract report.docx                    # 输出到 stdout
python3 docx_tools.py extract report.docx -o report.md       # 保存为 MD
python3 docx_tools.py extract report.docx --split-chapters   # 按章节拆分
python3 docx_tools.py extract report.docx --json             # JSON 格式（含样式元数据）

# 格式校验
python3 docx_tools.py check snapshot report.docx              # 当前格式快照
python3 docx_tools.py check compare before.docx after.docx   # 对比两个版本

# 修订标记
python3 docx_tools.py track-changes read report.docx          # 读取修订内容
python3 docx_tools.py track-changes review report.docx -o reviewed.docx --rules rules.json
```

### docx_to_md.sh — DOCX 转 Markdown

通过 markitdown 或 pandoc 将 Word 转为 Markdown。支持多文件。

```bash
./docx_to_md.sh report.docx
./docx_to_md.sh *.docx                              # 批量
```

### pptx_tools.py — PPT 标准化工具

PPT 字体统一（微软雅黑）、文本格式修正、表格样式统一，或一键全做。

**场景**: 汇报 PPT 字体五花八门，需要统一成公司标准。

```bash
python3 pptx_tools.py font deck.pptx                # 字体→微软雅黑
python3 pptx_tools.py format deck.pptx               # 标点修正
python3 pptx_tools.py table deck.pptx                # 表格样式
python3 pptx_tools.py all deck.pptx                  # 全部
```

### pptx_to_md.py — PPT 转 Markdown

提取 PPT 幻灯片文本和备注为 Markdown。

```bash
python3 pptx_to_md.py presentation.pptx
python3 pptx_to_md.py presentation.pptx -o docs/
python3 pptx_to_md.py -r ./presentations/            # 递归处理目录
```

### report_quality_check.py — 报告质量检查

检查 Markdown 报告中的常见问题：禁用词（"确保"、"我们"）、残留要点列表、数据无来源标注、重复行、编号列表。支持自动修复。

**场景**: 投标文档提交前的质量自检。

```bash
python3 report_quality_check.py report.md             # 检查
python3 report_quality_check.py report.md --fix       # 自动修复
python3 report_quality_check.py report.md --bid       # 加标书评分对齐检查
python3 report_quality_check.py report.md --preview   # 预览修复方案
```

### scan_sensitive_words.py — AI 敏感词扫描

用 Claude 扫描投标文档，检测竞争对手公司名、不当措辞、跨项目名称污染。

**场景**: 标书复用时忘记替换上个项目的公司名，提交前 AI 扫一遍。

```bash
python3 scan_sensitive_words.py docs/
python3 scan_sensitive_words.py docs/ --json          # JSON 输出
python3 scan_sensitive_words.py docs/ --update        # 更新敏感词库
```

### bullet_to_paragraph.py — AI 要点转公文段落

用 Claude 将 Markdown 要点列表转换为正式公文段落或表格。

**场景**: 会议纪要是要点形式，需要转成正式报告的段落。

```bash
python3 bullet_to_paragraph.py notes.md               # 就地转换
python3 bullet_to_paragraph.py notes.md --dry-run     # 预览
python3 bullet_to_paragraph.py docs/                   # 批量处理目录
```

### chart.py — 数据驱动图表生成

从 JSON 配置生成柱状图、甘特图、流程图（matplotlib），以及将 Markdown 中的 ASCII art 替换为 PNG 引用。

**场景**: 报告中需要插入进度甘特图或数据柱状图，用 JSON 定义数据后一键生成。

```bash
python3 chart.py bar config.json -o bar.png           # 柱状图
python3 chart.py gantt config.json -o gantt.png       # 甘特图
python3 chart.py flow config.json -o flow.png         # 流程图
python3 chart.py insert docs/ --fix                   # ASCII art→PNG 替换
python3 chart.py bar --example                        # 查看示例配置
```

---

## Data Conversion — `scripts/data/` (4 scripts)

### convert.py — 统一格式转换

9 个子命令覆盖 CSV、TXT、XLSX、XLS 之间的互转，以及企业编码去重。

**场景**: 拿到一个 XLS 老格式文件需要转成 XLSX；或 CSV 和 TXT 之间互转。

```bash
python3 convert.py xlsx-from-xls old.xls              # XLS→XLSX
python3 convert.py xlsx-from-csv data.csv              # CSV→XLSX
python3 convert.py xlsx-to-csv data.xlsx               # XLSX→CSV
python3 convert.py csv-from-txt data.txt               # TXT→CSV
python3 convert.py csv-merge-txt dir/                  # 合并多个 TXT 到一个 CSV
python3 convert.py encode-duplicates companies.xlsx    # 企业重复编码去重
```

### xlsx_lowercase.py — Excel 英文转小写

将 Excel 中所有英文文本转为小写（跳过前两行表头）。

**场景**: 数据导入要求字段小写，批量处理 Excel。

```bash
python3 xlsx_lowercase.py data.xlsx                   # 输出 data_lower.xlsx
```

### xlsx_merge_tables.py — AI 表格合并

通过模糊匹配或 AI 匹配，将多个 Excel 表按名称字段合并。

**场景**: 两个表有相同实体但名称写法不同（"浙江水利" vs "浙江省水利厅"），需要智能匹配后合并数据。

```bash
python3 xlsx_merge_tables.py --master main.xlsx --master-key "名称" \
  --aux lookup.xlsx --aux-key "工程名称" --map "目标列=源列" -o merged.xlsx
```

### xlsx_splitsheets.py — Excel 按 Sheet 拆分

将多 Sheet 工作簿拆成独立文件。

**场景**: 收到一个包含 20 个区县数据的工作簿，需要拆成独立文件分发。

```bash
python3 xlsx_splitsheets.py workbook.xlsx             # 每个 Sheet 一个文件
python3 xlsx_splitsheets.py workbook.xlsx --workers 4  # 并行处理
```

---

## File Management — `scripts/file/` (5 scripts)

### downloads_organizer.py — 下载目录自动整理

按文件扩展名将下载目录中的文件分类到子目录。

**场景**: Downloads 堆了几百个文件，一键按类型（文档/图片/压缩包/安装包）归类。

```bash
python3 downloads_organizer.py                        # 整理 ~/Downloads
python3 downloads_organizer.py --dry-run              # 预览不移动
python3 downloads_organizer.py --scan-archive         # 含归档目录
```

### smart_rename.py — AI 智能重命名

用 Claude 分析文件名，按项目/主题分组，检测重复，生成重命名方案。

**场景**: Downloads 里一堆 "未命名.pdf"、"报告(1).docx"、"IMG_2024.jpg"，让 AI 识别内容并重命名。

```bash
python3 smart_rename.py analyze --all                 # 分析所有分类
python3 smart_rename.py analyze --dir ~/Downloads/docs # 分析指定目录
python3 smart_rename.py execute                       # 执行重命名
python3 smart_rename.py rollback                      # 回滚
```

### file_copy.py — 复制文件名/内容到剪贴板

从 Finder 选中的文件复制文件名或文件内容到剪贴板。

```bash
python3 file_copy.py name                             # 复制文件名
python3 file_copy.py content                          # 复制文件名+内容
```

### file_print.py — 打印文件

从 Finder 选中文件发送到打印机。

```bash
python3 file_print.py                                 # 打印 1 份
python3 file_print.py 3                               # 打印 3 份
```

### folder_paste.sh — 粘贴到 Finder

将剪贴板中的文件粘贴到 Finder 当前目录。

```bash
./folder_paste.sh                                     # 在 Finder 中选择目标目录后运行
```

---

## System Automation — `scripts/system/` (5 scripts)

### sys_app_launcher.py — 应用启动器

读取配置文件中的必备应用列表，检查哪些未运行，一键启动。

**场景**: 每天开机后一键启动工作所需的所有应用。

```bash
python3 sys_app_launcher.py                           # 读取 ~/Desktop/essential_apps.txt
```

### display_1080.sh / display_4k.sh — 显示器分辨率切换

通过 displayplacer 切换外接显示器分辨率。

**场景**: 投屏演示时切 1080p，回到工位切 4K。

```bash
./display_1080.sh                                     # 切 1920×1080
./display_4k.sh                                       # 切 3840×2160
```

### create_reminder.sh — 创建 macOS 提醒

通过 AppleScript 在"提醒事项"App 中创建提醒。

```bash
./create_reminder.sh "周五交报告" "2026-04-04 17:00" "工作"
```

### dingtalk_gov.sh — 启动政务钉钉

启动政务钉钉客户端（跳过已运行检查）。

```bash
./dingtalk_gov.sh
```

---

## Network Proxy — `scripts/network/` (6 scripts)

ClashX Pro 代理管理，全部通过 Raycast 快捷键调用。

| 脚本 | 功能 | Raycast 关键词 |
|------|------|---------------|
| `clashx_enhanced.sh` | 切换 TUN 增强模式 | ClashX Enhanced |
| `clashx_mode_rule.sh` | 切换到规则模式 | ClashX Rule |
| `clashx_mode_global.sh` | 切换到全局模式 | ClashX Global |
| `clashx_mode_direct.sh` | 切换到直连模式 | ClashX Direct |
| `clashx_status.sh` | 查看当前状态 | ClashX Status |
| `clashx_proxy.sh` | 开关系统代理 | ClashX Proxy |

---

## Window Management — `scripts/window/` (1 script)

### yabai.py — Yabai 窗口管理

控制 Yabai 平铺窗口管理器：浮动切换、鼠标跟随焦点、窗口整理、服务开关。

```bash
python3 yabai.py float                                # 当前窗口浮动/平铺切换
python3 yabai.py mouse                                # 鼠标跟随焦点开关
python3 yabai.py org                                  # 整理当前空间窗口
python3 yabai.py toggle                               # 启停 yabai 服务
```

---

## Developer Tools — `scripts/tools/` (7 scripts)

### llm_client.py — LLM 统一调用模块

通过 `claude` CLI 调用 LLM，支持模型选择。是其他 AI 脚本的基础依赖。

```python
from tools.llm_client import chat
response = chat("你是一个翻译助手", "翻译这段话", model="haiku")
```

### cc_sessions.py — Claude Code 会话管理

索引 Claude Code 会话历史，支持 AI 摘要生成和 Markdown 导出。

**场景**: 回顾过去一周的 Claude Code 对话，导出为 Markdown 归档。

```bash
python3 cc_sessions.py index --summarize              # 建索引 + AI 摘要
python3 cc_sessions.py export --date-from 2026-03-01  # 导出指定日期后的会话
python3 cc_sessions.py export --project Dev-scripts   # 导出特定项目的会话
```

### git_smart_push.py — 智能批量 Git 推送

批量 commit + push 多个 repo，支持 AI 生成 commit message 或简单时间戳。

**场景**: 每天下班前一键同步所有项目到 GitHub。

```bash
python3 git_smart_push.py                             # AI 生成 commit message
python3 git_smart_push.py --simple                    # 用 "sync: 时间戳" 作为 message
python3 git_smart_push.py --all                       # 推送所有 repo（默认只推 auto_push=true 的）
```

### git_auto_stage.sh — Git 自动暂存 Hook

Claude Code PostToolUse hook，文件修改后自动 `git add`。

### memory_sync.sh — Memory 同步 Hook

Claude Code PostToolUse hook，将 `~/.claude/projects/` 下的 memory 文件同步到 `~/docs/memory/`。

### tts_volcano.py — 火山引擎文字转语音

调用字节跳动火山引擎 TTS API，将文本合成语音。

```bash
python3 tts_volcano.py "你好世界" -o hello.mp3
python3 tts_volcano.py "文本" -v zh_female_shuangkuai_moon_bigtts  # 指定音色
python3 tts_volcano.py "文本" --no-play               # 不自动播放
```

### app_open.py — Finder 选中文件用编辑器打开

在 Finder 中选中文件/文件夹后，用指定编辑器打开。

```bash
python3 app_open.py cursor                            # 用 Cursor 打开
python3 app_open.py terminal                          # 用终端打开
python3 app_open.py nvim                              # 用 Nvim 打开
```

---

## Repo Management — `repo_manager.py`

GitHub 仓库批量管理：推广（更新 description/topics/homepage）、审计（检查 README 结构、gitignore、依赖）、截图。

```bash
python3 repo_manager.py promote hydro-rainfall hydro-geocode  # 批量推广
python3 repo_manager.py audit scripts dockit                  # 审计项目
python3 repo_manager.py screenshot streamlit hydro-rainfall https://rainfall.tianlizeng.cloud
python3 repo_manager.py screenshot cli cclog "cclog stats"
```

---

## Shared Libraries — `lib/`

| 模块 | 功能 |
|------|------|
| `clipboard.py` | 剪贴板读写（macOS pbcopy/pbpaste） |
| `display.py` | 终端输出格式化（成功/错误/警告/信息） |
| `file_ops.py` | 文件扩展名检查、存在性验证 |
| `finder.py` | macOS Finder 交互（AppleScript 获取选中文件） |
| `progress.py` | 进度追踪（成功/失败/跳过计数） |
| `usage_log.py` | 脚本使用统计记录 |
| `env.py` | 环境配置、路径检测、Raycast 环境变量加载 |
| `docx_xml.py` | Word XML 命名空间常量 |
| `clashx.sh` | ClashX Pro API 辅助函数 |
| `common.sh` | Raycast Shell 脚本公共库 |
| `hydraulic/` | 水利领域库（河流编码、流域代码、QGIS 配置、Streamlit 组件） |

### Maintenance Tools — `lib/tools/`

| 工具 | 功能 | 用法 |
|------|------|------|
| `health_check.py` | 项目完整性验证（断链、import、语法） | `python3 lib/tools/health_check.py` |
| `cf_api.py` | Cloudflare DNS/Access API | `python3 lib/tools/cf_api.py dns list` |
| `gen_claude_md.py` | AI 批量生成 CLAUDE.md | `python3 lib/tools/gen_claude_md.py` |
| `sync_index.py` | 脚本索引生成 | `python3 lib/tools/sync_index.py` |
| `vps_cmd.py` | VPS SSH 操作 | `python3 lib/tools/vps_cmd.py status` |
| `validate_raycast_commands.py` | Raycast 命令校验 | `python3 lib/tools/validate_raycast_commands.py` |

---

## Project Structure

```
scripts/
├── scripts/               # 40 utility scripts
│   ├── document/   (13)   # Word/Markdown/PPT processing
│   ├── data/        (4)   # Excel/CSV/TXT conversion
│   ├── file/        (5)   # File organization & management
│   ├── system/      (5)   # macOS system automation
│   ├── network/     (6)   # ClashX proxy management
│   ├── tools/       (6)   # Developer tools (Git, LLM, TTS)
│   └── window/      (1)   # Yabai window management
├── lib/                   # Shared libraries
│   ├── hydraulic/         # Water engineering domain
│   └── tools/       (6)   # Maintenance tools
├── projects/
│   └── company_query/     # Tianyancha enterprise query (CLI)
├── raycast/
│   ├── commands/          # Shell wrappers with @raycast metadata
│   └── lib/               # Shared runner scripts
├── templates/             # Document templates (gitignored)
├── repo_manager.py        # GitHub repo management
└── docs/                  # Documentation & dependency map
```

## Related

- [dockit](https://github.com/zengtianli/dockit) — Document processing toolkit
- [scripts-archive](https://github.com/zengtianli/scripts-archive) — Retired scripts

## License

MIT

---

<a id="中文"></a>

# Scripts（中文）

macOS 个人效率工具脚本库，共 40 个脚本，覆盖文档处理、数据转换、文件管理、系统自动化等。通过 [Raycast](https://raycast.com/) 集成快捷命令。

上方英文文档包含每个脚本的详细功能说明、使用场景和完整命令示例。

## 许可证

MIT
