# Scripts

![macOS](https://img.shields.io/badge/platform-macOS-lightgrey) ![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Raycast](https://img.shields.io/badge/Raycast-integrated-orange)

**English** | [中文](#中文)

A collection of 70+ macOS utility scripts and 12 projects for document processing, data conversion, file management, system automation, and hydraulic engineering. Integrated with [Raycast](https://raycast.com/) for quick access via 58 script commands.

## Features

| Category | Scripts | Description |
|----------|---------|-------------|
| `scripts/document/` | 23 | Word/Markdown/PPT formatting, conversion, quality check |
| `scripts/file/` | 12 | File organization, batch rename, downloads cleanup |
| `scripts/data/` | 5 | Excel/CSV/TXT conversion and processing |
| `scripts/system/` | 9 | App launcher, usage tracking, display management |
| `scripts/network/` | 6 | ClashX proxy management |
| `scripts/tools/` | 14 | TTS, Gantt charts, Git automation, AI tools |
| `scripts/window/` | 1 | Yabai window management |

### Projects (Streamlit Apps & CLI Tools)

| Project | Type | Description |
|---------|------|-------------|
| `capacity` | Streamlit | Water pollution capacity calculator |
| `geocode` | Streamlit | Geocoding with Amap API |
| `reservoir_schedule` | Streamlit | Reservoir dispatch scheduling |
| `irrigation` | Streamlit | Irrigation water demand |
| `district_scheduler` | Streamlit | Regional scheduling |
| `water_efficiency` | Streamlit | Water use efficiency analysis |
| `risk_data` | CLI | Risk analysis table generator |
| `company_query` | CLI | Company info query (Tianyancha API) |
| `qgis` | Pipeline | QGIS spatial processing scripts |

## Quick Start

```bash
# Clone
git clone https://github.com/zengtianli/scripts.git
cd scripts

# Install dependencies
pip3 install -r requirements.txt

# Run health check
python3 lib/tools/health_check.py
```

### Raycast Integration

1. Open Raycast Settings (Cmd + ,)
2. Go to Extensions > Script Commands
3. Add script directory: `<your-path>/scripts/raycast/commands`
4. Refresh — 58 commands ready to use

### Environment Variables

Copy `.env.example` and fill in your API keys:

```bash
cp .env.example .env
```

| Variable | Required By | Description |
|----------|-------------|-------------|
| `TIANYANCHA_API_TOKEN` | company_query | Tianyancha API token |
| `AMAP_API_KEY` | geocode | Amap (Gaode) Maps API key |

## Project Structure

```
scripts/
├── scripts/           # Utility scripts by category
│   ├── data/          # Data conversion (xlsx, csv, txt)
│   ├── document/      # Document processing (docx, md, pptx)
│   ├── file/          # File operations
│   ├── system/        # System tools
│   ├── network/       # Network proxy (ClashX)
│   ├── window/        # Window management (Yabai)
│   └── tools/         # Misc tools (TTS, Git, AI)
├── lib/               # Shared libraries
│   ├── core/          # Core processors (csv, docx, xlsx)
│   ├── hydraulic/     # Hydraulic engineering utilities
│   └── tools/         # Health check, index sync
├── projects/          # Multi-file projects (Streamlit/CLI)
├── raycast/           # Raycast script commands (58 commands)
│   ├── commands/      # Shell wrappers with Raycast metadata
│   └── lib/           # Shared runner scripts
└── templates/         # Document templates
```

## Related

- [dockit](https://github.com/zengtianli/dockit) — Document processing toolkit. Some document scripts in this repo use `dockit.text` under the hood.

## License

MIT

---

<a id="中文"></a>

# Scripts（中文）

macOS 个人效率工具脚本库，包含 70+ 个功能脚本和 12 个项目，覆盖文档处理、数据转换、文件管理、系统自动化和水利工程等领域。通过 [Raycast](https://raycast.com/) 集成 58 个快捷命令。

## 功能分类

| 分类 | 数量 | 说明 |
|------|------|------|
| `scripts/document/` | 23 | Word/Markdown/PPT 格式化、转换、质量检查 |
| `scripts/file/` | 12 | 文件整理、批量重命名、下载目录清理 |
| `scripts/data/` | 5 | Excel/CSV/TXT 转换处理 |
| `scripts/system/` | 9 | 应用启动器、使用追踪、显示器管理 |
| `scripts/network/` | 6 | ClashX 代理管理 |
| `scripts/tools/` | 14 | TTS、甘特图、Git 自动化、AI 工具 |
| `scripts/window/` | 1 | Yabai 窗口管理 |

### 项目（Streamlit 应用 & CLI 工具）

| 项目 | 类型 | 说明 |
|------|------|------|
| `capacity` | Streamlit | 纳污能力计算 |
| `geocode` | Streamlit | 地理编码（高德 API） |
| `reservoir_schedule` | Streamlit | 水库调度 |
| `irrigation` | Streamlit | 灌溉需水量 |
| `district_scheduler` | Streamlit | 区域调度 |
| `water_efficiency` | Streamlit | 用水效率分析 |
| `risk_data` | CLI | 风险分析表填充 |
| `company_query` | CLI | 企业信息查询（天眼查 API） |
| `qgis` | Pipeline | QGIS 空间处理脚本 |

## 快速开始

```bash
# 克隆
git clone https://github.com/zengtianli/scripts.git
cd scripts

# 安装依赖
pip3 install -r requirements.txt

# 运行健康检查
python3 lib/tools/health_check.py
```

### Raycast 集成

1. 打开 Raycast 设置（Cmd + ,）
2. 进入 Extensions > Script Commands
3. 添加脚本目录：`<你的路径>/scripts/raycast/commands`
4. 刷新 — 58 个命令即可使用

### 环境变量

复制 `.env.example` 并填入你的 API 密钥：

```bash
cp .env.example .env
```

| 变量 | 用于 | 说明 |
|------|------|------|
| `TIANYANCHA_API_TOKEN` | company_query | 天眼查 API Token |
| `AMAP_API_KEY` | geocode | 高德地图 API Key |

## 许可证

MIT
