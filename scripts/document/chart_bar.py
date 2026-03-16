#!/usr/bin/env python3
"""
数据驱动的条形/柱状统计图生成脚本

输入 JSON 配置文件，输出 PNG 统计图。
支持水平条形图、垂直柱状图、堆叠图、分组对比图。

JSON 配置格式见 --example 输出。
"""

import sys
import json
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_info
from file_ops import show_version_info

from chart_common import (
    setup_chinese_fonts, get_phase_color, save_figure,
    GRID_COLOR, BG_COLOR, DEFAULT_DPI,
    CHART_VERSION, CHART_AUTHOR, CHART_UPDATED,
)

SCRIPT_NAME = "chart_bar"

EXAMPLE_CONFIG = """{
  "title": "2024年杭州市用水结构",
  "type": "horizontal",
  "unit": "亿m³",
  "show_total": true,
  "total_label": "合计",
  "items": [
    {"label": "生活用水（含公共）", "value": 13.69, "percent": 46.9},
    {"label": "农业用水", "value": 9.90, "percent": 33.9},
    {"label": "工业用水", "value": 4.45, "percent": 15.2},
    {"label": "生态环保用水", "value": 1.18, "percent": 4.0}
  ],
  "figsize": [12, 6],
  "dpi": 300
}"""


def draw_horizontal_bar(config: dict, output_path: str):
    """水平条形图（如用水结构）"""
    chinese_font = setup_chinese_fonts()

    items = config["items"]
    title = config.get("title", "统计图")
    unit = config.get("unit", "")
    figsize = tuple(config.get("figsize", [12, 6]))
    dpi = config.get("dpi", DEFAULT_DPI)
    show_total = config.get("show_total", False)

    labels = [it["label"] for it in items]
    values = [it["value"] for it in items]
    percents = [it.get("percent") for it in items]
    colors = [it.get("color") or get_phase_color(i) for i, it in enumerate(items)]

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    y_pos = np.arange(len(items))
    bars = ax.barh(y_pos, values, height=0.55, color=colors,
                   edgecolor="#333333", linewidth=0.8, alpha=0.9)

    # 条内/条右标注
    max_val = max(values)
    for i, (bar, val) in enumerate(zip(bars, values)):
        pct = percents[i]
        if pct is not None:
            label_text = f"{val} {unit}（{pct}%）"
        else:
            label_text = f"{val} {unit}"

        if val > max_val * 0.3:
            ax.text(val / 2, i, label_text, ha="center", va="center",
                    fontsize=10, fontweight="bold", color="white")
        else:
            ax.text(val + max_val * 0.01, i, label_text, ha="left",
                    va="center", fontsize=9, color="#333333")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    # 合计标注
    if show_total:
        total_val = sum(values)
        total_label = config.get("total_label", "合计")
        ax.text(0.98, 0.02, f"{total_label}：{total_val:.2f} {unit}",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=11, fontweight="bold", color="#666666",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                         edgecolor="#CCCCCC", alpha=0.9))

    ax.grid(True, axis="x", color=GRID_COLOR, linestyle="-",
            linewidth=0.6, alpha=0.7)
    ax.grid(False, axis="y")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"条形图已生成: {output_path}")


def draw_vertical_bar(config: dict, output_path: str):
    """垂直柱状图"""
    chinese_font = setup_chinese_fonts()

    items = config["items"]
    title = config.get("title", "统计图")
    unit = config.get("unit", "")
    figsize = tuple(config.get("figsize", [12, 7]))
    dpi = config.get("dpi", DEFAULT_DPI)

    labels = [it["label"] for it in items]
    values = [it["value"] for it in items]
    colors = [it.get("color") or get_phase_color(i) for i, it in enumerate(items)]

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    x_pos = np.arange(len(items))
    bars = ax.bar(x_pos, values, width=0.55, color=colors,
                  edgecolor="#333333", linewidth=0.8, alpha=0.9)

    # 柱顶标注
    for bar, val in zip(bars, values):
        pct_item = next((it for it in items if it["value"] == val), None)
        pct = pct_item.get("percent") if pct_item else None
        if pct is not None:
            text = f"{val}\n({pct}%)"
        else:
            text = f"{val}"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                text, ha="center", va="bottom", fontsize=9,
                fontweight="bold", color="#333333")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_ylabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    ax.grid(True, axis="y", color=GRID_COLOR, linestyle="-",
            linewidth=0.6, alpha=0.7)
    ax.grid(False, axis="x")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"柱状图已生成: {output_path}")


def draw_grouped_bar(config: dict, output_path: str):
    """分组对比柱状图（多系列）"""
    chinese_font = setup_chinese_fonts()

    groups = config["groups"]
    series = config["series"]
    title = config.get("title", "对比图")
    unit = config.get("unit", "")
    figsize = tuple(config.get("figsize", [14, 7]))
    dpi = config.get("dpi", DEFAULT_DPI)

    n_groups = len(groups)
    n_series = len(series)
    bar_width = 0.8 / n_series
    x = np.arange(n_groups)

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    for i, s in enumerate(series):
        offset = (i - n_series / 2 + 0.5) * bar_width
        color = s.get("color") or get_phase_color(i)
        bars = ax.bar(x + offset, s["values"], bar_width * 0.9,
                      label=s["name"], color=color, edgecolor="#333333",
                      linewidth=0.6, alpha=0.9)
        for bar, val in zip(bars, s["values"]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height(), f"{val}",
                    ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10, fontweight="bold")
    ax.set_ylabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.legend(fontsize=10, framealpha=0.9)

    ax.grid(True, axis="y", color=GRID_COLOR, linestyle="-",
            linewidth=0.6, alpha=0.7)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"分组柱状图已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="数据驱动的统计图生成（JSON → PNG）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s bar_config.json -o 用水结构.png
  %(prog)s --example
""",
    )
    parser.add_argument("config", nargs="?", help="JSON 配置文件")
    parser.add_argument("-o", "--output", help="输出 PNG 路径")
    parser.add_argument("--example", action="store_true", help="打印示例配置")
    parser.add_argument("--version", action="store_true", help="版本信息")

    args = parser.parse_args()

    if args.version:
        show_version_info(SCRIPT_NAME, CHART_VERSION, CHART_AUTHOR, CHART_UPDATED)
        return

    if args.example:
        print(EXAMPLE_CONFIG)
        return

    if not args.config:
        parser.print_help()
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        show_error(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    output = args.output or str(config_path.parent / "bar.png")
    show_info(f"读取配置: {config_path}")

    chart_type = config.get("type", "horizontal")
    if chart_type == "horizontal":
        draw_horizontal_bar(config, output)
    elif chart_type == "vertical":
        draw_vertical_bar(config, output)
    elif chart_type == "grouped":
        draw_grouped_bar(config, output)
    else:
        show_error(f"不支持的图表类型: {chart_type}（可选: horizontal/vertical/grouped）")
        sys.exit(1)


if __name__ == "__main__":
    main()
