# useful_scripts

macOS 个人效率工具脚本库，主要通过 Raycast 调用。

## 目录结构

```
scripts/              # 功能脚本，按类别分组
├── document/         # 文档处理（docx_ + md_ + pptx_）
├── data/             # 数据转换（xlsx_ + csv_）
├── file/             # 文件操作（file_ + folder_）
├── system/           # 系统工具（sys_ + display_）
├── network/          # 网络代理（clashx_）
├── window/           # 窗口管理（yabai_）
└── tools/            # 杂项工具（tts, app_open, git_smart_push, llm_client）

lib/                  # 统一公共库
├── hydraulic/        # 水利领域专用库（编码映射、QGIS 配置）
├── tools/            # 项目维护工具（health_check, sync_index, cf_api, gen_claude_md）
├── asr/              # 语音识别词表数据
└── *.py / *.sh       # 公共模块（display, file_ops, finder, progress, docx_xml 等）

projects/             # 复杂多文件项目（内部自治）
└── company_query/    # 企业查询（CLI）

templates/            # 模板文件（zdwp_template.docx 等）

raycast/              # Raycast 入口
├── commands/         # Shell wrapper 脚本（统一入口）
└── lib/              # 运行器（run_python.sh → 调用 lib/common.sh）

_index/               # 脚本索引（by-function, by-platform, by-type）
```

## Claude CLI 依赖脚本

以下脚本通过 `scripts/tools/llm_client.py` 调用 `claude -p`：

| 脚本 | 功能 | 模型 |
|------|------|------|
| `document/bullet_to_paragraph.py` | 要点转公文段落/表格 | haiku |
| `document/frontmatter_gen.py` | 批量生成 MD frontmatter | haiku |
| `document/scan_sensitive_words.py` | 标书敏感词检测 | haiku |
| `document/session_indexer.py` | CC 会话索引（--summarize 时） | haiku |
| `file/smart_rename.py` | AI 驱动文件重命名 | haiku |
| `tools/git_smart_push.py` | 智能 commit message 生成 | haiku |
| `lib/tools/gen_claude_md.py` | 批量生成 CLAUDE.md | sonnet |

`llm_client.py` 接口：`chat(system, message, model="haiku")` → `claude -p --model <model>`

## 开发约定

### 引用路径
- Shell 引用库：`source "$(dirname "$0")/../../lib/xxx.sh"`
- `scripts/xxx/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))`
- `projects/xxx/` 下的 Python 脚本：`sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))`
- 水利领域导入：`from hydraulic import ...`
- LLM 调用：`from tools.llm_client import chat`

### 命名规则
- 脚本保留功能前缀：`docx_`、`xlsx_`、`csv_`、`md_`、`pptx_`、`yabai_`、`clashx_`
- 文件/文件夹操作：`file_`、`folder_`
- 系统工具：`sys_`、`display_`
- 秘书系统：`sec_`（secretary）
- 水利领域：`hy_`（hydraulic）

### Raycast 脚本
- `raycast/commands/` 下是 Shell wrapper（含 @raycast 元数据）
- Wrapper 通过 `run_python.sh` 调用实际脚本：`run_python "document/docx_text_formatter.py"`
- 新增脚本时需同步创建对应的 wrapper

### 项目元数据
- `projects/` 下每个项目需有 `_project.yaml` 文件

## 注意事项

- 批量修改脚本时，必须逐一检查每个脚本的所有外部引用（source/import），不能只搜索已知模式
- 恢复或删除文件时，必须处理所有关联文件（主文件、wrapper、raycast 引用）
- 修改完成后，运行 `python3 lib/tools/health_check.py` 验证
- 公共库只有一套（`lib/`），不要在项目内创建独立的 _lib 目录

## 路径规范

**当前目录结构**（2026-03-31 清理后）：
- ✅ `scripts/{data,document,file,network,secretary,system,tools,window}/` - 功能脚本
- ✅ `raycast/commands/` - Raycast 入口脚本
- ❌ `execute/` - 已删除
- ❌ `.assets/scripts/` - 已删除
- ❌ `lib/core/` - 已删除（未使用）
- ❌ `lib/common.py` / `lib/common_utils.py` - 已删除（deprecated shim）

**跨仓库路径引用**：
- 水利公司：`~/Work/zdwp/`
- 论文部：`~/Personal/essays/`
- 个人网站：`~/Personal/website/`
- 求职管理：`~/Personal/resume/`
- 工作报告：`~/Work/reports/`
- 学习笔记：`~/Learn/`
