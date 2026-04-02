#!/usr/bin/env python3
"""
Unified repository management tool — promote, audit, and screenshot repos.

Subcommands:
    promote     Batch GitHub promotion (README, SVG, metadata)
    audit       Audit ~/Dev projects against gold standard template
    screenshot  Take screenshots of repos (Streamlit, CLI, Tauri)

Usage:
    python3 repo_manager.py promote
    python3 repo_manager.py audit [project ...] [--fix-gitignore]
    python3 repo_manager.py screenshot streamlit <repo> <url>
    python3 repo_manager.py screenshot cli <repo> "<command>" [title]
    python3 repo_manager.py screenshot tauri <repo>
    python3 repo_manager.py screenshot batch [--include-cli]
"""

import argparse
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from textwrap import dedent

# ═════════════════════════════════════════════════════════════
# Shared constants
# ═════════════════════════════════════════════════════════════

DEV = Path.home() / "Dev"


# ═════════════════════════════════════════════════════════════
#
#   SECTION 1: PROMOTE — batch GitHub promotion
#
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Repo metadata (promote)
# ─────────────────────────────────────────────

PROMOTE_REPOS = {
    "hydro-rainfall": {
        "description": "Rainfall-runoff calculator for lake irrigation — 6-step pipeline across 228 lakes",
        "topics": ["hydrology", "rainfall", "runoff", "streamlit", "python", "water-resources"],
        "demo_url": "https://hydro-rainfall.tianlizeng.cloud",
        "tagline_en": "Rainfall-runoff calculator for lake irrigation demand — processes 228 lakes across 15 partitions.",
        "tagline_cn": "湖泊灌区降雨径流计算工具——覆盖 15 个分区、228 个湖泊的径流推算。",
        "features_en": [
            ("6-step pipeline", "partition → area → rainfall coefficient → intake → deduction → merge"),
            ("228 lakes / 15 partitions", "Pre-loaded spatial dataset, no manual upload needed"),
            ("Daily → hourly conversion", "Converts daily precipitation data into hourly time series"),
            ("Batch processing", "Upload multi-file ZIP for bulk computation"),
            ("Excel export", "Download results per lake with full breakdowns"),
        ],
        "features_cn": [
            ("6 步处理流程", "分区 → 面积 → 径流系数 → 引水量 → 扣损 → 合并"),
            ("228 个湖泊 / 15 个分区", "内置空间数据集，无需手动上传"),
            ("日→时转换", "将日降水数据转换为逐小时时序"),
            ("批量处理", "上传 ZIP 压缩包批量计算"),
            ("Excel 导出", "按湖泊下载含完整明细的计算结果"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Rainfall",
        "svg_subtitle": "Rainfall-Runoff Calculator",
        "svg_items": ["分区选择  ▼ 分区一", "湖泊数量  228", "径流系数  0.65", "[计算]  [导出 Excel]"],
    },
    "hydro-geocode": {
        "description": "Batch geocoder using Amap API — address↔coordinates conversion and POI search",
        "topics": ["geocoding", "amap", "gis", "python", "streamlit", "coordinate-conversion"],
        "demo_url": "https://hydro-geocode.tianlizeng.cloud",
        "tagline_en": "Batch geocoding tool powered by Amap API — forward/reverse geocoding and POI company search.",
        "tagline_cn": "基于高德地图 API 的批量地理编码工具——正/逆向解析与 POI 企业查询。",
        "features_en": [
            ("Forward geocoding", "Address text → WGS-84 / GCJ-02 coordinates"),
            ("Reverse geocoding", "Coordinates → formatted address"),
            ("POI search", "Find company locations by name and city"),
            ("Coordinate conversion", "WGS-84 ↔ GCJ-02 ↔ BD-09 system conversion"),
            ("Batch via Excel/CSV", "Upload spreadsheet, download enriched results"),
        ],
        "features_cn": [
            ("正向地理编码", "地址文本 → WGS-84 / GCJ-02 坐标"),
            ("逆向地理编码", "坐标 → 格式化地址"),
            ("POI 企业查询", "按名称和城市查找企业位置"),
            ("坐标系转换", "WGS-84 ↔ GCJ-02 ↔ BD-09 互转"),
            ("Excel/CSV 批量处理", "上传表格，下载带坐标的结果"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Geocode",
        "svg_subtitle": "Batch Geocoder · Amap API",
        "svg_items": ["模式  ▼ 正向编码", "输入地址  杭州市西湖区...", "结果  120.1234, 30.2345", "[批量处理]  [导出]"],
    },
    "hydro-district": {
        "description": "Daily supply-demand scheduling for 19 river districts with reservoir/sluice management",
        "topics": ["hydrology", "water-resources", "scheduling", "streamlit", "python", "district-management"],
        "demo_url": "https://hydro-district.tianlizeng.cloud",
        "tagline_en": "Daily water supply-demand scheduling across 19 river districts with reservoir and sluice gate management.",
        "tagline_cn": "面向 19 个河湖分区的逐日供需调度模型，支持水库与闸门精细化管理。",
        "features_en": [
            ("19-district model", "Individual parameters per district for accurate local scheduling"),
            ("Daily scheduling", "Day-by-day supply-demand balance with operations log"),
            ("Reservoir & sluice control", "Manage inflow, outflow, gate operations per timestep"),
            ("Batch import/export", "ZIP-based multi-district data workflow"),
            ("Result browser", "Built-in viewer for district-specific outputs"),
        ],
        "features_cn": [
            ("19 分区模型", "各分区独立参数，精准本地化调度"),
            ("逐日调度", "逐日供需平衡，含操作日志"),
            ("水库与闸门控制", "管理每个时步的入流、出流和闸门操作"),
            ("批量导入/导出", "基于 ZIP 的多分区数据工作流"),
            ("结果浏览器", "内置分区专属输出查看器"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro District",
        "svg_subtitle": "Supply-Demand Scheduling",
        "svg_items": ["分区  ▼ 分区 03", "时段  2024-01 ~ 2024-12", "供水量  1,240 万m³", "[运行调度]  [下载结果]"],
    },
    "hydro-risk": {
        "description": "ETL pipeline for hydrological risk mapping — GeoJSON to Excel risk assessment workbooks",
        "topics": ["hydrology", "risk-assessment", "etl", "gis", "python", "streamlit"],
        "demo_url": None,
        "tagline_en": "3-phase ETL pipeline that converts GeoJSON hydrological data into structured Excel risk assessment workbooks.",
        "tagline_cn": "三阶段 ETL 流水线——将 GeoJSON 水文数据转换为结构化 Excel 风险评估工作簿。",
        "features_en": [
            ("Phase 1 — Database build", "Extract GeoJSON features into normalized base tables"),
            ("Phase 2 — Forecasting", "Apply hydraulic models to generate forecast data"),
            ("Phase 3 — Risk analysis", "Compute risk scores and produce 18+ sheet workbooks"),
            ("14 processing scripts", "Modular pipeline, each step independently runnable"),
            ("Auto code generation", "Generates lookup codes and normalizes spatial data"),
        ],
        "features_cn": [
            ("第一阶段 — 建库", "从 GeoJSON 特征中提取并规范化基础表"),
            ("第二阶段 — 预测", "应用水力模型生成预测数据"),
            ("第三阶段 — 风险分析", "计算风险评分，生成 18+ 工作表的工作簿"),
            ("14 个处理脚本", "模块化流水线，每步可独立运行"),
            ("自动编码生成", "生成查找代码并规范化空间数据"),
        ],
        "svg_type": "terminal",
        "svg_title": "hydro-risk pipeline",
        "svg_lines": [
            ("❯", "python 01_build_database.py", "cmd"),
            ("", "[Phase 1] Building base tables from GeoJSON...", "info"),
            ("", "  ✓ 14 feature tables extracted", "green"),
            ("❯", "python 02_forecast.py", "cmd"),
            ("", "[Phase 2] Running hydraulic forecast...", "info"),
            ("", "  ✓ Forecast data generated (3,240 records)", "green"),
            ("❯", "python 03_risk_analysis.py", "cmd"),
            ("", "[Phase 3] Computing risk scores...", "info"),
            ("", "  ✓ Risk workbook saved: risk_report_2024.xlsx (18 sheets)", "green"),
        ],
    },
    "hydro-irrigation": {
        "description": "Daily water balance calculator for paddy and dryland crop irrigation demand",
        "topics": ["irrigation", "water-balance", "agriculture", "python", "streamlit", "hydrology"],
        "demo_url": "https://hydro-irrigation.tianlizeng.cloud",
        "tagline_en": "Daily water balance model for agricultural irrigation — separate calculation for paddy and dryland crops.",
        "tagline_cn": "农业灌溉逐日水量平衡模型——水稻与旱作物独立计算。",
        "features_en": [
            ("Paddy water balance", "Day-by-day rice paddy irrigation demand with ponding depth tracking"),
            ("Dryland crop model", "Separate soil moisture balance for non-paddy crops"),
            ("Multi-zone support", "Process multiple irrigation zones in a single run"),
            ("Batch via ZIP", "Upload multiple input files as a single archive"),
            ("Excel export", "Per-zone results with daily irrigation schedules"),
        ],
        "features_cn": [
            ("水稻水量平衡", "逐日水稻灌溉需水量，追踪田间水深"),
            ("旱作物模型", "非水稻作物独立土壤水分平衡"),
            ("多分区支持", "单次运行处理多个灌区"),
            ("ZIP 批量处理", "将多个输入文件打包上传"),
            ("Excel 导出", "含逐日灌溉计划的分区结果"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Irrigation",
        "svg_subtitle": "Irrigation Water Demand",
        "svg_items": ["作物类型  ▼ 水稻", "灌区数量  8", "计算时段  2024 年生长季", "[计算需水量]  [导出 Excel]"],
    },
    "hydro-annual": {
        "description": "Zhejiang Province water resources annual report query tool (2019–2024)",
        "topics": ["hydrology", "water-resources", "annual-report", "python", "streamlit", "zhejiang"],
        "demo_url": "https://hydro-annual.tianlizeng.cloud",
        "tagline_en": "Query and export Zhejiang Province water resources annual reports from 2019 to 2024.",
        "tagline_cn": "浙江省水资源年报数据查询与导出工具，涵盖 2019—2024 年。",
        "features_en": [
            ("Multi-year coverage", "Browse water resource data from 2019 to 2024"),
            ("City-level filter", "Filter by prefecture-level city across Zhejiang"),
            ("Category selection", "Choose specific report categories for targeted queries"),
            ("Export Excel / CSV", "Download filtered results in your preferred format"),
            ("Pre-loaded dataset", "No file upload needed — data is built in"),
        ],
        "features_cn": [
            ("多年数据", "浏览 2019—2024 年水资源数据"),
            ("地市筛选", "按浙江各地级市过滤"),
            ("报告类别", "选择特定报告类别精准查询"),
            ("导出 Excel / CSV", "以您偏好的格式下载过滤结果"),
            ("内置数据集", "无需上传文件，数据已内嵌"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Annual",
        "svg_subtitle": "浙江省水资源年报查询",
        "svg_items": ["年份  ▼ 2023", "城市  ▼ 杭州市", "类别  ▼ 地表水资源", "共 142 条记录  [导出 Excel]"],
    },
    "hydro-efficiency": {
        "description": "Industrial park water efficiency assessment using AHP+CRITIC+TOPSIS methodology",
        "topics": ["water-efficiency", "ahp", "topsis", "python", "streamlit", "industrial"],
        "demo_url": "https://hydro-efficiency.tianlizeng.cloud",
        "tagline_en": "Industrial park water use efficiency assessment — AHP+CRITIC combined weighting with TOPSIS ranking.",
        "tagline_cn": "工业园区水资源利用效率评价——AHP+CRITIC 组合赋权 + TOPSIS 综合排名。",
        "features_en": [
            ("AHP + CRITIC weighting", "Adjustable α blends subjective and objective weights"),
            ("3-tier assessment", "Park-wide → pipeline → enterprise level evaluation"),
            ("TOPSIS ranking", "Enterprise scoring and classification ranking"),
            ("Pre-loaded sample data", "Ready to use without any file uploads"),
            ("Excel template export", "Download blank template for your own data"),
        ],
        "features_cn": [
            ("AHP + CRITIC 赋权", "可调 α 参数融合主客观权重"),
            ("三层评价体系", "园区 → 管网 → 企业级评价"),
            ("TOPSIS 排名", "企业评分与等级排名"),
            ("内置样例数据", "无需上传即可直接使用"),
            ("Excel 模板导出", "下载空白模板填入自有数据"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Efficiency",
        "svg_subtitle": "Water Efficiency Assessment",
        "svg_items": ["α 权重  0.5  ←●→", "评价层级  ▼ 企业级", "企业 A  综合得分 0.82  优", "[运行评价]  [导出报告]"],
    },
    "hydro-reservoir": {
        "description": "Cascade reservoir hydropower scheduling optimizer with Plotly visualizations",
        "topics": ["reservoir", "hydropower", "scheduling", "python", "streamlit", "plotly"],
        "demo_url": "https://hydro-reservoir.tianlizeng.cloud",
        "tagline_en": "Cascade reservoir hydropower scheduling optimizer with interactive Plotly charts.",
        "tagline_cn": "梯级水库水电优化调度工具，内置 Plotly 交互式可视化图表。",
        "features_en": [
            ("Cascade scheduling", "Joint optimization across multiple reservoirs in series"),
            ("Flexible time step", "Daily, 10-day, or monthly calculation intervals"),
            ("Interactive charts", "Plotly visualizations of water levels, flow, and power output"),
            ("Parameter preview", "Inspect reservoir parameters before running optimization"),
            ("Excel I/O", "Upload input workbooks and download scheduling results"),
        ],
        "features_cn": [
            ("梯级联合调度", "对串联多库进行联合优化"),
            ("灵活时步", "逐日、旬或月计算时段"),
            ("交互式图表", "Plotly 可视化水位、流量和出力"),
            ("参数预览", "运行优化前查看水库参数"),
            ("Excel 输入/输出", "上传输入工作簿，下载调度结果"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Reservoir",
        "svg_subtitle": "Cascade Hydropower Scheduling",
        "svg_items": ["水库数量  3", "时步  ▼ 旬", "目标函数  最大发电量", "[开始优化]  [查看图表]"],
    },
    "hydro-capacity": {
        "description": "River and reservoir pollution receiving capacity calculator with multi-scenario support",
        "topics": ["pollution-capacity", "water-quality", "environment", "python", "streamlit", "hydrology"],
        "demo_url": "https://hydro-capacity.tianlizeng.cloud",
        "tagline_en": "Pollution receiving capacity calculator for rivers and reservoirs — multi-scenario, tributary segmentation.",
        "tagline_cn": "河流与水库纳污能力计算工具——多方案情景、支流分段建模。",
        "features_en": [
            ("Multi-scheme scenarios", "Model multiple pollution scenarios side-by-side"),
            ("Tributary segmentation", "Independent parameters per tributary reach"),
            ("Monthly computation", "Incorporate monthly flow data for seasonal variation"),
            ("Excel I/O", "Upload parameters, download capacity results"),
            ("Pre-loaded samples", "Ready-to-run example datasets included"),
        ],
        "features_cn": [
            ("多方案情景", "并排模拟多个污染情景"),
            ("支流分段", "每条支流独立参数设置"),
            ("逐月计算", "结合月径流数据体现季节变化"),
            ("Excel 输入/输出", "上传参数，下载纳污能力结果"),
            ("内置样例数据", "含开箱即用的示例数据集"),
        ],
        "svg_type": "streamlit",
        "svg_title": "Hydro Capacity",
        "svg_subtitle": "Pollution Receiving Capacity",
        "svg_items": ["河段  ▼ 干流 + 3 条支流", "污染物  ▼ COD", "纳污能力  1,840 t/a", "[计算]  [多方案对比]"],
    },
    "hydro-qgis": {
        "description": "QGIS spatial processing pipeline for river cross-sections, dike clipping, and hydraulic GIS tasks",
        "topics": ["qgis", "gis", "hydraulics", "python", "water-resources", "spatial-analysis"],
        "demo_url": None,
        "tagline_en": "13-step QGIS pipeline for hydraulic engineering GIS tasks — cross-sections, dike clipping, spatial processing.",
        "tagline_cn": "13 步 QGIS 水利工程 GIS 流水线——横断面生成、堤防裁剪与空间处理。",
        "features_en": [
            ("River cross-section generation", "Automatically generate cross-section lines from centerline and DEM"),
            ("Dike / levee clipping", "Clip spatial features along dike alignments"),
            ("13-step numbered pipeline", "Sequential scripts, each independently runnable"),
            ("Utility library", "Reusable hydraulic-specific QGIS helper functions"),
            ("Shell orchestration", "Run full pipeline or individual steps via shell scripts"),
        ],
        "features_cn": [
            ("河道横断面生成", "从中心线和 DEM 自动生成横断面"),
            ("堤防裁剪", "沿堤线裁剪空间要素"),
            ("13 步编号流水线", "顺序脚本，每步可独立运行"),
            ("工具函数库", "可复用的水利专项 QGIS 辅助函数"),
            ("Shell 编排脚本", "通过 Shell 脚本运行完整流水线或单步"),
        ],
        "svg_type": "terminal",
        "svg_title": "hydro-qgis pipeline",
        "svg_lines": [
            ("❯", "python 01_generate_river_points.py", "cmd"),
            ("", "  ✓ River centerline points generated (1,240 pts)", "green"),
            ("❯", "python 05_generate_cross_sections.py", "cmd"),
            ("", "  ✓ Cross sections created: 248 lines", "green"),
            ("❯", "python 09_clip_dike_features.py", "cmd"),
            ("", "  ✓ Dike features clipped to study area", "green"),
            ("❯", "python 13_export_results.py", "cmd"),
            ("", "  ✓ GeoJSON + SHP exported to ./output/", "green"),
            ("", "  Pipeline complete.", "blue"),
        ],
    },
    "downloads-organizer": {
        "description": "Auto-organizer for your Downloads folder — sorts files by type with real-time watching",
        "topics": ["file-management", "automation", "macos", "cross-platform", "python", "cli"],
        "demo_url": None,
        "tagline_en": "Automatically organize your Downloads folder by file type — with real-time watching and dry-run preview.",
        "tagline_cn": "按文件类型自动整理下载目录——支持实时监控与预演模式。",
        "features_en": [
            ("Real-time watching", "Monitor Downloads folder and sort new files as they arrive"),
            ("One-click organize", "Manually trigger sorting of all existing files"),
            ("Dry-run preview", "See what would be moved before committing any changes"),
            ("Customizable categories", "8 built-in types (Images, Docs, Archives…) + fully configurable"),
            ("Cross-platform", "Runs on macOS, Windows, and Linux"),
        ],
        "features_cn": [
            ("实时监控", "监控下载目录，新文件到达即自动整理"),
            ("一键整理", "手动触发对所有现有文件的分类"),
            ("预演模式", "在实际移动前预览将要执行的操作"),
            ("可自定义分类", "8 种内置类型（图片、文档、压缩包等）+ 完全可配置"),
            ("跨平台", "支持 macOS、Windows 和 Linux"),
        ],
        "svg_type": "terminal",
        "svg_title": "downloads-organizer",
        "svg_lines": [
            ("❯", "downloads-organizer --dry-run", "cmd"),
            ("", "Dry run mode — no files will be moved", "yellow"),
            ("", "  [move] report_2024.pdf  →  Documents/", "info"),
            ("", "  [move] photo_holiday.jpg  →  Images/", "info"),
            ("", "  [move] setup.dmg  →  Installers/", "info"),
            ("", "  12 files would be organized", "green"),
            ("❯", "downloads-organizer --watch", "cmd"),
            ("", "Watching ~/Downloads for new files...", "blue"),
            ("", "  ✓ archive.zip  →  Archives/", "green"),
        ],
    },
}


# ─────────────────────────────────────────────
# SVG generators (promote)
# ─────────────────────────────────────────────

def _make_streamlit_svg(title: str, subtitle: str, items: list[str]) -> str:
    """Generate a browser/Streamlit app mockup SVG."""
    item_lines = ""
    y = 200
    for item in items:
        item_lines += f'  <text x="40" y="{y}" font-family="SF Mono,Fira Code,monospace" font-size="13" fill="#cdd6f4">{item}</text>\n'
        y += 28

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360" viewBox="0 0 720 360">
  <!-- Window background -->
  <rect width="720" height="360" rx="10" fill="#1e1e2e"/>
  <!-- Title bar (browser chrome) -->
  <rect width="720" height="40" rx="10" fill="#313244"/>
  <rect y="20" width="720" height="20" fill="#313244"/>
  <!-- Dots -->
  <circle cx="20" cy="20" r="6" fill="#f38ba8"/>
  <circle cx="40" cy="20" r="6" fill="#f9e2af"/>
  <circle cx="60" cy="20" r="6" fill="#a6e3a1"/>
  <!-- Address bar -->
  <rect x="90" y="10" width="480" height="20" rx="4" fill="#45475a"/>
  <text x="330" y="24" text-anchor="middle" font-family="SF Mono,monospace" font-size="11" fill="#6c7086">localhost:8501</text>
  <!-- Sidebar -->
  <rect x="0" y="40" width="180" height="320" fill="#181825"/>
  <!-- Sidebar title -->
  <text x="90" y="75" text-anchor="middle" font-family="SF Mono,monospace" font-size="14" font-weight="bold" fill="#89b4fa">{title}</text>
  <text x="90" y="95" text-anchor="middle" font-family="SF Mono,monospace" font-size="10" fill="#6c7086">{subtitle}</text>
  <!-- Sidebar menu items -->
  <rect x="10" y="110" width="160" height="24" rx="4" fill="#313244"/>
  <text x="90" y="126" text-anchor="middle" font-family="SF Mono,monospace" font-size="11" fill="#a6e3a1">▶ 主功能</text>
  <text x="90" y="160" text-anchor="middle" font-family="SF Mono,monospace" font-size="11" fill="#6c7086">📊 结果查看</text>
  <text x="90" y="185" text-anchor="middle" font-family="SF Mono,monospace" font-size="11" fill="#6c7086">⚙ 参数设置</text>
  <!-- Main content area -->
  <rect x="180" y="40" width="540" height="320" fill="#1e1e2e"/>
  <!-- Content header -->
  <text x="220" y="80" font-family="SF Mono,monospace" font-size="16" font-weight="bold" fill="#cdd6f4">{subtitle}</text>
  <line x1="200" y1="92" x2="700" y2="92" stroke="#45475a" stroke-width="1"/>
  <!-- Dynamic content items -->
{item_lines}
  <!-- Bottom status bar -->
  <rect x="180" y="330" width="540" height="30" fill="#181825"/>
  <text x="220" y="349" font-family="SF Mono,monospace" font-size="10" fill="#6c7086">Python 3.11  |  Streamlit 1.36  |  MIT License</text>
</svg>"""


def _make_terminal_svg(title: str, lines: list[tuple]) -> str:
    """Generate a terminal window SVG. lines = [(prompt, text, style), ...]"""
    STYLES = {
        "cmd": "#cdd6f4",
        "info": "#89dceb",
        "green": "#a6e3a1",
        "yellow": "#f9e2af",
        "blue": "#89b4fa",
    }
    content = ""
    y = 75
    for prompt, text, style in lines:
        color = STYLES.get(style, "#cdd6f4")
        prompt_color = "#89b4fa" if prompt else "#313244"
        if prompt:
            content += f'  <text x="20" y="{y}" font-family="SF Mono,Fira Code,monospace" font-size="13" fill="{prompt_color}">{prompt}</text>\n'
            content += f'  <text x="36" y="{y}" font-family="SF Mono,Fira Code,monospace" font-size="13" fill="{color}">{text}</text>\n'
        else:
            content += f'  <text x="20" y="{y}" font-family="SF Mono,Fira Code,monospace" font-size="13" fill="{color}">{text}</text>\n'
        y += 24

    height = max(280, y + 30)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="{height}" viewBox="0 0 720 {height}">
  <rect width="720" height="{height}" rx="10" fill="#1e1e2e"/>
  <rect width="720" height="36" rx="10" fill="#313244"/>
  <rect y="18" width="720" height="18" fill="#313244"/>
  <circle cx="18" cy="18" r="6" fill="#f38ba8"/>
  <circle cx="38" cy="18" r="6" fill="#f9e2af"/>
  <circle cx="58" cy="18" r="6" fill="#a6e3a1"/>
  <text x="360" y="23" text-anchor="middle" font-family="SF Mono,monospace" font-size="12" fill="#6c7086">{title}</text>
{content}
</svg>"""


# ─────────────────────────────────────────────
# README generators (promote)
# ─────────────────────────────────────────────

def _make_readme_en(name: str, meta: dict) -> str:
    url = meta["demo_url"]
    img_ext = "png" if url else "svg"

    lines = [
        f"# {name}",
        "",
        "**English** | [中文](README_CN.md)",
        "",
        meta["tagline_en"],
        "",
    ]

    if url:
        domain = url.replace("https://", "")
        lines.append(f'[![Live Demo](https://img.shields.io/badge/Live_Demo-{domain.replace("-", "--")}-blue?style=for-the-badge)]({url})')
    lines.append('[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge)](https://python.org)')
    lines.append('[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)')
    lines.append("")

    if url:
        lines += ["---", "", "### Try it now — no install needed", "", f"**{url}**", ""]

    lines += [
        "---",
        "",
        f"![{name} demo](docs/screenshots/demo.{img_ext})",
        "",
        "---",
        "",
        f"## What can {name} do?",
        "",
        "| Feature | Description |",
        "|---------|-------------|",
    ]
    for f, d in meta["features_en"]:
        lines.append(f"| **{f}** | {d} |")

    if name == "downloads-organizer":
        install_cmd = f"pip install {name}"
    else:
        install_cmd = f"git clone https://github.com/zengtianli/{name}.git\ncd {name}\npip install -r requirements.txt"

    quickstart = "downloads-organizer --watch" if name == "downloads-organizer" else "streamlit run app.py"

    lines += [
        "",
        "## Install",
        "",
        "```bash",
        install_cmd,
        "```",
        "",
        "## Quick Start",
        "",
        "```bash",
        quickstart,
        "```",
        "",
    ]

    if url:
        lines += [
            "## Self-host",
            "",
            "```bash",
            f"git clone https://github.com/zengtianli/{name}.git",
            f"cd {name}",
            "pip install -r requirements.txt",
            "streamlit run app.py",
            "```",
            "",
            f"Or use the hosted version: **{url}**",
            "",
        ]

    streamlit_req = "Streamlit 1.36+" if (url or name not in ["downloads-organizer", "hydro-qgis"]) else "See requirements.txt"
    lines += [
        "## Requirements",
        "",
        "- Python 3.9+",
        f"- {streamlit_req}",
        "",
        "## License",
        "",
        "MIT",
        "",
    ]

    return "\n".join(lines)


def _make_readme_cn(name: str, meta: dict) -> str:
    url = meta["demo_url"]
    img_ext = "png" if url else "svg"

    lines = [
        f"# {name}",
        "",
        "[English](README.md) | **中文**",
        "",
        meta["tagline_cn"],
        "",
    ]

    if url:
        domain = url.replace("https://", "")
        lines.append(f'[![在线演示](https://img.shields.io/badge/在线演示-{domain.replace("-", "--")}-blue?style=for-the-badge)]({url})')
    lines.append('[![Python 3.9+](https://img.shields.io/badge/Python-3.9+-yellow?style=for-the-badge)](https://python.org)')
    lines.append('[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)')
    lines.append("")

    if url:
        lines += ["---", "", "### 无需安装，立即体验", "", f"**{url}**", ""]

    lines += [
        "---",
        "",
        f"![{name} demo](docs/screenshots/demo.{img_ext})",
        "",
        "---",
        "",
        "## 功能一览",
        "",
        "| 功能 | 说明 |",
        "|------|------|",
    ]
    for f, d in meta["features_cn"]:
        lines.append(f"| **{f}** | {d} |")

    if name == "downloads-organizer":
        install_cmd = f"pip install {name}"
    else:
        install_cmd = f"git clone https://github.com/zengtianli/{name}.git\ncd {name}\npip install -r requirements.txt"

    quickstart = "downloads-organizer --watch" if name == "downloads-organizer" else "streamlit run app.py"

    lines += [
        "",
        "## 安装",
        "",
        "```bash",
        install_cmd,
        "```",
        "",
        "## 快速开始",
        "",
        "```bash",
        quickstart,
        "```",
        "",
    ]

    if url:
        lines += [
            "## 自托管",
            "",
            "```bash",
            f"git clone https://github.com/zengtianli/{name}.git",
            f"cd {name}",
            "pip install -r requirements.txt",
            "streamlit run app.py",
            "```",
            "",
            f"或直接使用托管版本：**{url}**",
            "",
        ]

    streamlit_req = "Streamlit 1.36+" if (url or name not in ["downloads-organizer", "hydro-qgis"]) else "详见 requirements.txt"
    lines += [
        "## 环境要求",
        "",
        "- Python 3.9+",
        f"- {streamlit_req}",
        "",
        "## License",
        "",
        "MIT",
        "",
    ]

    return "\n".join(lines)


# ─────────────────────────────────────────────
# Git & GitHub helpers (promote)
# ─────────────────────────────────────────────

def _promote_run(cmd: str, cwd: str = None, check: bool = True):
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {cmd}\n{result.stderr}")
    return result.stdout.strip()


def _promote_process_repo(name: str, meta: dict, tmp_base: Path):
    print(f"\n{'='*60}")
    print(f"  {name}")
    print(f"{'='*60}")

    repo_dir = tmp_base / name

    # Clone
    if repo_dir.exists():
        shutil.rmtree(repo_dir)
    print(f"  Cloning...")
    _promote_run(f"git clone https://github.com/zengtianli/{name}.git {repo_dir}")

    # Create docs/screenshots/
    screenshots_dir = repo_dir / "docs" / "screenshots"
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    # Generate SVG
    if meta["svg_type"] == "streamlit":
        svg = _make_streamlit_svg(meta["svg_title"], meta["svg_subtitle"], meta["svg_items"])
    else:
        svg = _make_terminal_svg(meta["svg_title"], meta["svg_lines"])

    (screenshots_dir / "demo.svg").write_text(svg, encoding="utf-8")
    print(f"  ✓ SVG generated")

    # Generate READMEs
    (repo_dir / "README.md").write_text(_make_readme_en(name, meta), encoding="utf-8")
    (repo_dir / "README_CN.md").write_text(_make_readme_cn(name, meta), encoding="utf-8")
    print(f"  ✓ README.md + README_CN.md written")

    # Commit & push
    _promote_run("git add README.md README_CN.md docs/screenshots/demo.svg", cwd=str(repo_dir))

    # Check if there's anything to commit
    status = _promote_run("git status --porcelain", cwd=str(repo_dir))
    if not status:
        print(f"  ✓ Nothing to commit, skipping push")
    else:
        _promote_run(
            'git commit -m "docs: add bilingual README, badges, and demo screenshot\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"',
            cwd=str(repo_dir)
        )
        _promote_run("git push", cwd=str(repo_dir))
        print(f"  ✓ Committed and pushed")

    # Update GitHub metadata
    topics_arg = " ".join(f"--add-topic {t}" for t in meta["topics"])
    _promote_run(f'gh repo edit zengtianli/{name} --description "{meta["description"]}" {topics_arg}')
    print(f"  ✓ GitHub description + topics updated")
    print(f"  → https://github.com/zengtianli/{name}")


def _promote_main():
    tmp_base = Path("/tmp/batch_promote")
    tmp_base.mkdir(exist_ok=True)

    total = len(PROMOTE_REPOS)
    success = 0

    for i, (name, meta) in enumerate(PROMOTE_REPOS.items(), 1):
        print(f"\n[{i}/{total}] Processing {name}...")
        try:
            _promote_process_repo(name, meta, tmp_base)
            success += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}")

    print(f"\n{'='*60}")
    print(f"Done: {success}/{total} repos promoted")
    print(f"{'='*60}")


# ═════════════════════════════════════════════════════════════
#
#   SECTION 2: AUDIT — project auditing
#
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Config (audit)
# ─────────────────────────────────────────────

# Projects to audit (skip private/experimental ones)
AUDIT_SKIP = {"configs", ".claude", ".DS_Store"}

GITIGNORE_BASELINE = {
    "# Python": ["__pycache__/", "*.py[cod]", "*.egg-info/", "dist/", "build/", "*.egg"],
    "# Virtual env": [".venv/", "venv/"],
    "# Environment": [".env"],
    "# IDE": [".idea/", ".vscode/"],
    "# OS": [".DS_Store"],
    "# Cache": [".pytest_cache/", ".ruff_cache/", ".mypy_cache/"],
}


# ─────────────────────────────────────────────
# Checkers (audit)
# ─────────────────────────────────────────────

def _audit_check_readme(project_dir: Path, lang: str = "en") -> list[str]:
    """Check README against gold standard template. Returns list of issues."""
    fname = "README.md" if lang == "en" else "README_CN.md"
    path = project_dir / fname
    issues = []

    if not path.exists():
        issues.append(f"Missing {fname}")
        return issues

    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    # 1. Language selector
    if lang == "en":
        if not any("**English**" in l and "中文" in l for l in lines[:5]):
            issues.append(f"{fname}: missing language selector (expected '**English** | [中文](README_CN.md)')")
    else:
        if not any("**中文**" in l and "English" in l for l in lines[:5]):
            issues.append(f"{fname}: missing language selector (expected '[English](README.md) | **中文**')")

    # 2. Badge style
    badge_lines = [l for l in lines if "img.shields.io/badge" in l]
    non_ftb = [l for l in badge_lines if "style=for-the-badge" not in l]
    if non_ftb:
        issues.append(f"{fname}: {len(non_ftb)} badge(s) not using for-the-badge style")

    # 3. Separator after badges
    if badge_lines:
        last_badge_idx = max(i for i, l in enumerate(lines) if "img.shields.io/badge" in l)
        # Look for --- within 3 lines after last badge
        found_sep = any(lines[j].strip() == "---" for j in range(last_badge_idx + 1, min(last_badge_idx + 4, len(lines))))
        if not found_sep:
            issues.append(f"{fname}: missing separator '---' after badges")

    # 4. Screenshot
    has_screenshot = any(re.search(r"!\[.*\]\(docs/screenshots/", l) for l in lines)
    if not has_screenshot:
        issues.append(f"{fname}: missing screenshot reference (docs/screenshots/)")

    # 5. Screenshot file exists
    if has_screenshot:
        screenshot_path = project_dir / "docs" / "screenshots" / "demo.png"
        homepage_path = project_dir / "docs" / "screenshots" / "homepage.png"
        if not screenshot_path.exists() and not homepage_path.exists():
            issues.append(f"{fname}: screenshot referenced but file not found in docs/screenshots/")

    # 6. Feature table
    has_table = any(l.strip().startswith("|") and "---" not in l and "|" in l[1:] for l in lines)
    if not has_table:
        issues.append(f"{fname}: missing feature table")

    # 7. Install section
    has_install = any(re.match(r"^#{1,3}\s*(Install|安装)", l) for l in lines)
    if not has_install:
        issues.append(f"{fname}: missing Install/安装 section")

    # 8. Quick Start section
    has_quickstart = any(re.match(r"^#{1,3}\s*(Quick Start|快速|Usage|使用|快速上手)", l) for l in lines)
    if not has_quickstart:
        issues.append(f"{fname}: missing Quick Start section")

    return issues


def _audit_check_gitignore(project_dir: Path) -> tuple[list[str], list[tuple[str, list[str]]]]:
    """Check .gitignore for baseline entries. Returns (issues, missing_sections)."""
    path = project_dir / ".gitignore"
    issues = []
    missing_sections = []

    if not path.exists():
        issues.append("Missing .gitignore")
        return issues, []

    content = path.read_text(encoding="utf-8")
    existing = set()
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            existing.add(stripped.rstrip("/"))

    for section, entries in GITIGNORE_BASELINE.items():
        section_missing = []
        for entry in entries:
            normalized = entry.rstrip("/")
            if normalized not in existing:
                section_missing.append(entry)
        if section_missing:
            missing_sections.append((section, section_missing))
            issues.append(f".gitignore: missing {len(section_missing)} entries from {section}")

    return issues, missing_sections


def _audit_check_deps(project_dir: Path) -> list[str]:
    """Check dependency version pinning."""
    issues = []
    req_path = project_dir / "requirements.txt"

    if req_path.exists():
        for line in req_path.read_text().strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            if ">=" not in line and "==" not in line and "~=" not in line:
                issues.append(f"requirements.txt: unpinned dependency '{line}'")

    return issues


def _audit_fix_gitignore(project_dir: Path, missing_sections: list[tuple[str, list[str]]]):
    """Append missing gitignore entries."""
    path = project_dir / ".gitignore"
    if not path.exists():
        return

    content = path.read_text(encoding="utf-8")
    if not content.endswith("\n"):
        content += "\n"

    append_lines = ["\n"]
    for comment, entries in missing_sections:
        append_lines.append(comment)
        for e in entries:
            append_lines.append(e)
        append_lines.append("")

    content += "\n".join(append_lines).rstrip() + "\n"
    path.write_text(content, encoding="utf-8")


# ─────────────────────────────────────────────
# Reporter (audit)
# ─────────────────────────────────────────────

def _audit_project(name: str, fix: bool = False) -> list[str]:
    """Run all checks on a single project. Returns list of issues."""
    project_dir = DEV / name
    if not project_dir.is_dir():
        return [f"Directory not found: {project_dir}"]

    all_issues = []

    # Detect project type
    has_python = any(project_dir.glob("*.py")) or (project_dir / "requirements.txt").exists()

    if has_python:
        # README checks
        all_issues.extend(_audit_check_readme(project_dir, "en"))
        all_issues.extend(_audit_check_readme(project_dir, "cn"))

        # Gitignore
        gi_issues, missing_sections = _audit_check_gitignore(project_dir)
        all_issues.extend(gi_issues)
        if fix and missing_sections:
            _audit_fix_gitignore(project_dir, missing_sections)
            all_issues.append(f".gitignore: ✓ FIXED ({sum(len(s) for _, s in missing_sections)} entries added)")

        # Dependencies
        all_issues.extend(_audit_check_deps(project_dir))

    return all_issues


def _audit_main(args):
    fix_gi = args.fix_gitignore
    targets = args.projects

    if not targets:
        # Auto-discover projects
        targets = sorted(
            d.name for d in DEV.iterdir()
            if d.is_dir() and not d.name.startswith(".") and d.name not in AUDIT_SKIP
        )

    total_issues = 0
    clean_count = 0

    for name in targets:
        issues = _audit_project(name, fix=fix_gi)
        if not issues:
            clean_count += 1
            continue

        print(f"\n{'─'*50}")
        print(f"  {name}")
        print(f"{'─'*50}")
        for issue in issues:
            marker = "  ✓" if "FIXED" in issue else "  ✗"
            print(f"{marker} {issue}")
        total_issues += len([i for i in issues if "FIXED" not in i])

    print(f"\n{'='*50}")
    print(f"Audited {len(targets)} projects: {clean_count} clean, {total_issues} issues found")
    if fix_gi:
        print(f"(--fix-gitignore applied)")
    print(f"{'='*50}")


# ═════════════════════════════════════════════════════════════
#
#   SECTION 3: SCREENSHOT — repo screenshot tool
#
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────
# Registry: repos with screenshot configs
# ─────────────────────────────────────────────

SCREENSHOT_REPOS = {
    # Streamlit apps (have live demo URLs)
    "hydro-rainfall":   {"type": "streamlit", "url": "https://hydro-rainfall.tianlizeng.cloud"},
    "hydro-geocode":    {"type": "streamlit", "url": "https://hydro-geocode.tianlizeng.cloud"},
    "hydro-district":   {"type": "streamlit", "url": "https://hydro-district.tianlizeng.cloud"},
    "hydro-irrigation": {"type": "streamlit", "url": "https://hydro-irrigation.tianlizeng.cloud"},
    "hydro-annual":     {"type": "streamlit", "url": "https://hydro-annual.tianlizeng.cloud"},
    "hydro-efficiency": {"type": "streamlit", "url": "https://hydro-efficiency.tianlizeng.cloud"},
    "hydro-reservoir":  {"type": "streamlit", "url": "https://hydro-reservoir.tianlizeng.cloud"},
    "hydro-capacity":   {"type": "streamlit", "url": "https://hydro-capacity.tianlizeng.cloud"},
    "hydro-toolkit":    {"type": "streamlit", "url": "https://hydro.tianlizeng.cloud"},
    "dockit":           {"type": "streamlit", "url": "https://dockit.tianlizeng.cloud"},
    "cclog":            {"type": "streamlit", "url": "https://cclog.tianlizeng.cloud"},

    # CLI tools (run command locally)
    "cc-harness":           {"type": "cli", "cmd": "python3 harness.py {DEV}/dockit", "title": "cc-harness"},
    "cc-context":           {"type": "cli", "cmd": "python3 context.py monitor",       "title": "cc-context"},
    "hydro-risk":           {"type": "cli", "cmd": "python3 01_build_database.py --help 2>&1 || echo 'hydro-risk pipeline'", "title": "hydro-risk"},
    "hydro-qgis":           {"type": "cli", "cmd": "python3 -c \"print('hydro-qgis pipeline')\"", "title": "hydro-qgis"},
    "downloads-organizer":  {"type": "cli", "cmd": "python3 -m downloads_organizer --help 2>&1 || echo 'downloads-organizer'", "title": "downloads-organizer"},

    # Tauri desktop apps (DMG in hydro-apps/release/)
    "hydro-apps": {
        "type": "tauri",
        "dmg_dir": "hydro-apps/release",
        "apps": {
            "水效评估工具": "efficiency",
            "纳污能力计算": "capacity",
            "水库群调度":   "reservoir",
            "水资源年报查询": "annual",
            "灌溉需水计算": "irrigation",
            "河区调度模型": "district",
            "地理编码工具": "geocode",
            "降雨数据分析": "rainfall",
        },
    },
}


# ─────────────────────────────────────────────
# Streamlit screenshot (via Playwright)
# ─────────────────────────────────────────────

def _screenshot_streamlit(url: str, out_path: Path) -> bool:
    """Take a Playwright screenshot of a live Streamlit app."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print(f"  Opening {url} ...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(url, timeout=30000)

            # Wait for Streamlit to finish rendering
            try:
                page.wait_for_selector(".stApp", timeout=20000)
            except Exception:
                pass

            # Extra wait for charts / dynamic content
            time.sleep(3)

            # Hide the Streamlit toolbar/deploy button
            page.evaluate("""
                const toolbar = document.querySelector('[data-testid="stToolbar"]');
                if (toolbar) toolbar.style.display = 'none';
                const deploy = document.querySelector('[data-testid="stDecoration"]');
                if (deploy) deploy.style.display = 'none';
            """)

            out_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()

        print(f"  ✓ Screenshot saved → {out_path.relative_to(DEV)}")
        return True

    except Exception as e:
        print(f"  ✗ Screenshot failed: {e}")
        return False


# ─────────────────────────────────────────────
# CLI screenshot (terminal-style rendering)
# ─────────────────────────────────────────────

_TERMINAL_HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head><style>
body {{ margin: 0; padding: 0; background: #0d1117; }}
.terminal {{
    background: #0d1117;
    color: #c9d1d9;
    font-family: 'SF Mono', 'Menlo', 'Monaco', 'Courier New', monospace;
    font-size: 13px;
    line-height: 1.5;
    padding: 20px 24px;
    min-height: 760px;
    box-sizing: border-box;
}}
.titlebar {{
    background: #161b22;
    border-bottom: 1px solid #30363d;
    padding: 8px 16px;
    display: flex;
    align-items: center;
    gap: 8px;
}}
.dot {{ width: 12px; height: 12px; border-radius: 50%; }}
.dot-red {{ background: #ff5f57; }}
.dot-yellow {{ background: #febc2e; }}
.dot-green {{ background: #28c840; }}
.title {{ color: #8b949e; margin-left: 12px; font-family: -apple-system, sans-serif; font-size: 13px; }}
b {{ color: #f0f6fc; }}
</style></head>
<body>
<div class="titlebar">
    <span class="dot dot-red"></span>
    <span class="dot dot-yellow"></span>
    <span class="dot dot-green"></span>
    <span class="title">{title}</span>
</div>
<pre class="terminal">{content}</pre>
</body>
</html>"""


def _screenshot_colorize_output(raw: str) -> str:
    """Apply terminal-style colors to CLI output."""
    escaped = html.escape(raw)
    colored = escaped
    colored = colored.replace('🔴', '<span style="color:#ff6b6b">🔴</span>')
    colored = colored.replace('🟡', '<span style="color:#ffd93d">🟡</span>')
    colored = colored.replace('🟢', '<span style="color:#6bcb77">🟢</span>')
    colored = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', colored)
    # Markdown headers
    colored = re.sub(
        r'^(#{1,3}) (.+)$',
        lambda m: f'<span style="color:#58a6ff;font-weight:bold">{"#"*len(m.group(1))} {m.group(2)}</span>',
        colored, flags=re.MULTILINE,
    )
    # Table separators
    colored = re.sub(
        r'^(\|[-|: ]+\|)$',
        lambda m: f'<span style="color:#555">{m.group(1)}</span>',
        colored, flags=re.MULTILINE,
    )
    return colored


def _screenshot_cli(cmd: str, cwd: str, out_path: Path, title: str = "Terminal") -> bool:
    """Run a CLI command, render output as terminal HTML, screenshot with Playwright."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("  ✗ playwright not installed. Run: pip install playwright && playwright install chromium")
        return False

    print(f"  Running: {cmd}")
    cmd_expanded = cmd.replace("{DEV}", str(DEV))
    result = subprocess.run(cmd_expanded, shell=True, cwd=cwd, capture_output=True, text=True)
    raw = result.stdout + result.stderr

    if not raw.strip():
        print("  ✗ Command produced no output")
        return False

    colored = _screenshot_colorize_output(raw)
    page_html = _TERMINAL_HTML_TEMPLATE.format(title=html.escape(title), content=colored)

    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w') as f:
        f.write(page_html)
        html_path = f.name

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1280, "height": 800})
            page.goto(f"file://{html_path}")
            time.sleep(0.5)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(out_path), full_page=False)
            browser.close()

        print(f"  ✓ Screenshot saved → {out_path.relative_to(DEV)}")
        return True

    except Exception as e:
        print(f"  ✗ Screenshot failed: {e}")
        return False

    finally:
        os.unlink(html_path)


# ─────────────────────────────────────────────
# Tauri desktop app screenshot (via screencapture -R)
# ─────────────────────────────────────────────

def _screenshot_tauri(config: dict, repo_dir: Path) -> bool:
    """Screenshot Tauri desktop apps by opening each, capturing the window region."""
    apps = config["apps"]  # {"中文名": "slug", ...}
    dmg_dir = DEV / config.get("dmg_dir", "")
    out_dir = repo_dir / "docs" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for app_name, slug in apps.items():
        out_path = out_dir / f"{slug}.png"
        print(f"\n  [{slug}] {app_name}")

        # Install from DMG if not in /Applications
        app_path = Path(f"/Applications/{app_name}.app")
        if not app_path.exists():
            dmg_file = dmg_dir / f"{slug}.dmg"
            if dmg_file.exists():
                print(f"    Installing from {dmg_file.name} ...")
                subprocess.run(["hdiutil", "attach", str(dmg_file), "-nobrowse", "-quiet"],
                               capture_output=True)
                # Find and copy the .app from the mounted volume
                vol = Path(f"/Volumes/{app_name}")
                if vol.exists():
                    found = list(vol.glob("*.app"))
                    if found:
                        subprocess.run(["cp", "-R", str(found[0]), "/Applications/"],
                                       capture_output=True)
                    subprocess.run(["hdiutil", "detach", str(vol), "-quiet"],
                                   capture_output=True)
            if not app_path.exists():
                print(f"    ✗ App not found: {app_path}")
                continue

        # Open app
        print(f"    Opening ...")
        subprocess.run(["open", "-a", app_name], capture_output=True)
        time.sleep(4)

        # Get window position and size via osascript
        try:
            pos = subprocess.run(
                ["osascript", "-e",
                 f'tell application "System Events" to tell process "{app_name}" to get position of window 1'],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()
            sz = subprocess.run(
                ["osascript", "-e",
                 f'tell application "System Events" to tell process "{app_name}" to get size of window 1'],
                capture_output=True, text=True, timeout=5,
            ).stdout.strip()

            if not pos or not sz:
                print(f"    ✗ Could not get window bounds")
                subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'],
                               capture_output=True)
                time.sleep(1)
                continue

            x, y = pos.split(", ")
            w, h = sz.split(", ")
        except Exception as e:
            print(f"    ✗ osascript error: {e}")
            subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'],
                           capture_output=True)
            time.sleep(1)
            continue

        # Capture window region (non-interactive, silent)
        subprocess.run(["screencapture", "-R", f"{x},{y},{w},{h}", "-x", str(out_path)])

        if out_path.exists() and out_path.stat().st_size > 0:
            print(f"    ✓ {out_path.relative_to(DEV)}")
            success += 1
        else:
            print(f"    ✗ Screenshot failed")

        # Close app
        subprocess.run(["osascript", "-e", f'tell application "{app_name}" to quit'],
                       capture_output=True)
        time.sleep(1)

    # Copy first screenshot as demo.png
    demo = out_dir / "demo.png"
    first_slug = list(apps.values())[0]
    first_shot = out_dir / f"{first_slug}.png"
    if first_shot.exists():
        import shutil as _shutil
        _shutil.copy2(first_shot, demo)
        print(f"\n  ✓ demo.png → {first_slug}.png")

    print(f"\n  Done: {success}/{len(apps)} apps screenshotted")
    return success > 0


# ─────────────────────────────────────────────
# Unified entry point (screenshot)
# ─────────────────────────────────────────────

def _screenshot_process_repo(name: str, config: dict = None) -> bool:
    """Take screenshot for a single repo using registry config or override."""
    config = config or SCREENSHOT_REPOS.get(name)
    if not config:
        print(f"  ✗ Unknown repo: {name}")
        return False

    repo_dir = DEV / name
    if not repo_dir.exists():
        print(f"  ✗ Directory not found: {repo_dir}")
        return False

    out_path = repo_dir / "docs" / "screenshots" / "demo.png"

    if config["type"] == "streamlit":
        return _screenshot_streamlit(config["url"], out_path)
    elif config["type"] == "cli":
        title = config.get("title", name)
        cmd = config["cmd"]
        return _screenshot_cli(cmd, str(repo_dir), out_path, f"{title} — {cmd.split()[0]} ...")
    else:
        print(f"  ✗ Unknown type: {config['type']}")
        return False


def _screenshot_update_readme_refs(repo_dir: Path, name: str):
    """Replace demo.svg with demo.png in README files."""
    for readme in ["README.md", "README_CN.md"]:
        path = repo_dir / readme
        if not path.exists():
            continue
        content = path.read_text(encoding="utf-8")
        new_content = content.replace(
            f"![{name} demo](docs/screenshots/demo.svg)",
            f"![{name} demo](docs/screenshots/demo.png)",
        )
        if new_content != content:
            path.write_text(new_content, encoding="utf-8")
            print(f"  ✓ Updated {readme}: demo.svg → demo.png")


def _screenshot_main(args):
    mode = args.screenshot_mode

    if mode == "streamlit":
        name, url = args.repo, args.url
        _screenshot_process_repo(name, {"type": "streamlit", "url": url})
        _screenshot_update_readme_refs(DEV / name, name)

    elif mode == "cli":
        name, cmd = args.repo, args.command
        title = args.title if args.title else name
        _screenshot_process_repo(name, {"type": "cli", "cmd": cmd, "title": title})

    elif mode == "tauri":
        name = args.repo
        config = SCREENSHOT_REPOS.get(name)
        if not config or config.get("type") != "tauri":
            print(f"  ✗ No tauri config for: {name}")
            sys.exit(1)
        repo_dir = DEV / name
        if not repo_dir.exists():
            print(f"  ✗ Directory not found: {repo_dir}")
            sys.exit(1)
        _screenshot_tauri(config, repo_dir)

    elif mode == "batch":
        include_cli = args.include_cli
        targets = list(SCREENSHOT_REPOS.keys())

        total = 0
        success = 0
        for name in targets:
            config = SCREENSHOT_REPOS.get(name)
            if not config:
                continue
            if config["type"] == "cli" and not include_cli:
                continue
            total += 1
            print(f"\n{'='*55}\n  [{total}] {name}\n{'='*55}")
            if _screenshot_process_repo(name, config):
                _screenshot_update_readme_refs(DEV / name, name)
                success += 1

        print(f"\n{'='*55}")
        print(f"Done: {success}/{total} repos screenshotted")
        print(f"{'='*55}")


# ═════════════════════════════════════════════════════════════
#
#   MAIN — argparse subcommands
#
# ═════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Unified repository management tool — promote, audit, and screenshot repos.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=dedent("""\
            Examples:
              %(prog)s promote
              %(prog)s audit
              %(prog)s audit cc-harness dockit --fix-gitignore
              %(prog)s screenshot streamlit hydro-rainfall https://hydro-rainfall.tianlizeng.cloud
              %(prog)s screenshot cli cc-harness "python3 harness.py ~/Dev/dockit"
              %(prog)s screenshot tauri hydro-apps
              %(prog)s screenshot batch --include-cli
        """),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── promote ──
    subparsers.add_parser("promote", help="Batch GitHub promotion (README, SVG, metadata)")

    # ── audit ──
    audit_parser = subparsers.add_parser("audit", help="Audit ~/Dev projects against gold standard template")
    audit_parser.add_argument("projects", nargs="*", help="Specific projects to audit (default: all)")
    audit_parser.add_argument("--fix-gitignore", action="store_true", help="Auto-fix gitignore gaps")

    # ── screenshot ──
    screenshot_parser = subparsers.add_parser("screenshot", help="Take screenshots of repos")
    ss_sub = screenshot_parser.add_subparsers(dest="screenshot_mode", required=True)

    # screenshot streamlit
    ss_streamlit = ss_sub.add_parser("streamlit", help="Screenshot a live Streamlit app")
    ss_streamlit.add_argument("repo", help="Repository name")
    ss_streamlit.add_argument("url", help="Live demo URL")

    # screenshot cli
    ss_cli = ss_sub.add_parser("cli", help="Screenshot a CLI tool by running a command")
    ss_cli.add_argument("repo", help="Repository name")
    ss_cli.add_argument("command", help="Command to run")
    ss_cli.add_argument("title", nargs="?", default=None, help="Window title (optional)")

    # screenshot tauri
    ss_tauri = ss_sub.add_parser("tauri", help="Screenshot Tauri desktop apps")
    ss_tauri.add_argument("repo", help="Repository name")

    # screenshot batch
    ss_batch = ss_sub.add_parser("batch", help="Screenshot all registered repos")
    ss_batch.add_argument("--include-cli", action="store_true", help="Include CLI tools in batch")

    args = parser.parse_args()

    if args.command == "promote":
        _promote_main()
    elif args.command == "audit":
        _audit_main(args)
    elif args.command == "screenshot":
        _screenshot_main(args)


if __name__ == "__main__":
    main()
