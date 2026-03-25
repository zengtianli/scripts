#!/usr/bin/env python3
"""
图表生成公共模块

提供中文字体设置、ZDWP 配色方案、统一输出参数等。
所有 chart_*.py 脚本共用。
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

# ── 版本信息 ──────────────────────────────────────────────────

CHART_VERSION = "1.0.0"
CHART_AUTHOR = "tianli"
CHART_UPDATED = "2026-03-14"

# ── 输出参数 ──────────────────────────────────────────────────

DEFAULT_DPI = 300
DEFAULT_FIGSIZE_GANTT = (16, 8)
DEFAULT_FIGSIZE_BAR = (12, 7)
DEFAULT_FIGSIZE_FLOW = (14, 10)

# ── ZDWP 配色方案 ────────────────────────────────────────────

# 阶段色板（最多 8 个阶段）
PHASE_COLORS = [
    "#2E86AB",  # 深蓝
    "#A23B72",  # 紫红
    "#F18F01",  # 橙色
    "#C73E1D",  # 红色
    "#3B7A57",  # 绿色
    "#6C5B7B",  # 灰紫
    "#45B7D1",  # 浅蓝
    "#F5A623",  # 黄色
]

# 里程碑颜色
MILESTONE_COLOR = "#E74C3C"
MILESTONE_EDGE = "#333333"

# 背景和网格
BG_COLOR = "#FAFAFA"
GRID_COLOR = "#E0E0E0"


# ── 中文字体 ──────────────────────────────────────────────────


def setup_chinese_fonts() -> FontProperties:
    """设置 matplotlib 中文字体支持（macOS 优先）"""
    font_candidates = [
        "Arial Unicode MS",
        "PingFang SC",
        "Microsoft YaHei",
        "SimHei",
        "DejaVu Sans",
    ]
    plt.rcParams.update(
        {
            "font.sans-serif": font_candidates,
            "axes.unicode_minus": False,
            "font.family": "sans-serif",
        }
    )
    mpl.rc("font", **{"sans-serif": font_candidates})

    # macOS 字体路径
    font_paths = [
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/PingFang.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            return FontProperties(fname=fp)
    return FontProperties()


def get_phase_color(index: int) -> str:
    """获取阶段颜色，循环使用"""
    return PHASE_COLORS[index % len(PHASE_COLORS)]


def save_figure(fig, output_path: str, dpi: int = DEFAULT_DPI):
    """统一保存图片"""
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor="white", edgecolor="none")
    plt.close(fig)
