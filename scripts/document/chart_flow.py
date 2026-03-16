#!/usr/bin/env python3
"""
数据驱动的流程框图 / 分层架构图生成脚本

输入 JSON 配置文件，输出 PNG 图。
支持两种模式：
  - layers: 分层架构图（从上到下或从左到右）
  - flow: 线性流程图（步骤→步骤→步骤）

JSON 配置格式见 --example 输出。
"""

import sys
import json
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_info
from file_ops import show_version_info

from chart_common import (
    setup_chinese_fonts, get_phase_color, save_figure,
    GRID_COLOR, BG_COLOR, DEFAULT_DPI,
    CHART_VERSION, CHART_AUTHOR, CHART_UPDATED,
)

SCRIPT_NAME = "chart_flow"

EXAMPLE_CONFIG = """{
  "title": "项目总体技术路线图",
  "type": "layers",
  "direction": "top-down",
  "layers": [
    {
      "name": "第一层：基础层（数据归集及清洗治理）",
      "boxes": [
        {"text": "水利监测\\n数据源"},
        {"text": "税务申报\\n数据源"},
        {"text": "用水统计\\n数据源"}
      ],
      "output": "高质量取用水数据集"
    },
    {
      "name": "第二层：核算层（取用水核算及水量平衡分析）",
      "boxes": [
        {"text": "全口径核算方法体系"},
        {"text": "《技术指南》编制"},
        {"text": "水量平衡分析功能"}
      ],
      "output": "核算成果 + 技术指南"
    }
  ],
  "figsize": [14, 10],
  "dpi": 300
}"""


def draw_layers(config: dict, output_path: str):
    """分层架构图"""
    chinese_font = setup_chinese_fonts()

    layers = config["layers"]
    title = config.get("title", "架构图")
    figsize = tuple(config.get("figsize", [14, 12]))
    dpi = config.get("dpi", DEFAULT_DPI)
    bottom_bar = config.get("bottom_bar", None)

    n_layers = len(layers)

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor("white")

    # 布局参数
    layer_height = 1.0
    layer_gap = 0.5
    total_height = n_layers * layer_height + (n_layers - 1) * layer_gap
    if bottom_bar:
        total_height += layer_height + layer_gap

    margin_x = 0.5
    canvas_width = 10.0
    box_margin = 0.3

    ax.set_xlim(-margin_x, canvas_width + margin_x)
    ax.set_ylim(-0.5, total_height + 1.0)
    ax.set_aspect("equal")
    ax.axis("off")

    # 标题
    ax.text(canvas_width / 2, total_height + 0.6, title,
            ha="center", va="center", fontsize=16, fontweight="bold")

    # 从上到下绘制层
    for layer_idx, layer in enumerate(layers):
        y_top = total_height - layer_idx * (layer_height + layer_gap)
        y_bottom = y_top - layer_height
        y_center = (y_top + y_bottom) / 2

        color = layer.get("color") or get_phase_color(layer_idx)

        # 层背景
        layer_bg = FancyBboxPatch(
            (0, y_bottom), canvas_width, layer_height,
            boxstyle="round,pad=0.05",
            facecolor=color, alpha=0.12,
            edgecolor=color, linewidth=1.5,
        )
        ax.add_patch(layer_bg)

        # 层标题（左上角）
        ax.text(0.2, y_top - 0.12, layer["name"],
                ha="left", va="top", fontsize=10,
                fontweight="bold", color=color)

        # 内部 box
        boxes = layer.get("boxes", [])
        if boxes:
            n_boxes = len(boxes)
            box_width = (canvas_width - box_margin * (n_boxes + 1)) / n_boxes
            box_h = 0.5
            box_y = y_center - box_h / 2 - 0.05

            for bi, box in enumerate(boxes):
                box_x = box_margin + bi * (box_width + box_margin)
                box_color = box.get("color", color)

                rect = FancyBboxPatch(
                    (box_x, box_y), box_width, box_h,
                    boxstyle="round,pad=0.08",
                    facecolor="white", edgecolor=box_color,
                    linewidth=1.2,
                )
                ax.add_patch(rect)
                ax.text(box_x + box_width / 2, box_y + box_h / 2,
                        box["text"], ha="center", va="center",
                        fontsize=9, fontweight="bold", color="#333333")

        # 输出标注
        output_text = layer.get("output")
        if output_text:
            ax.text(canvas_width - 0.2, y_bottom + 0.08, f"→ {output_text}",
                    ha="right", va="bottom", fontsize=8,
                    fontstyle="italic", color="#666666")

        # 层间箭头
        if layer_idx < n_layers - 1:
            arrow_y_start = y_bottom - 0.05
            arrow_y_end = y_bottom - layer_gap + 0.05
            ax.annotate(
                "", xy=(canvas_width / 2, arrow_y_end),
                xytext=(canvas_width / 2, arrow_y_start),
                arrowprops=dict(
                    arrowstyle="-|>", color="#666666",
                    lw=2, mutation_scale=20,
                ),
            )

    # 底部横条（如"平台对接"）
    if bottom_bar:
        bar_y = -0.3
        bar_h = 0.6
        bar_bg = FancyBboxPatch(
            (0, bar_y), canvas_width, bar_h,
            boxstyle="round,pad=0.05",
            facecolor="#555555", alpha=0.15,
            edgecolor="#555555", linewidth=1.5,
        )
        ax.add_patch(bar_bg)
        ax.text(canvas_width / 2, bar_y + bar_h / 2, bottom_bar,
                ha="center", va="center", fontsize=10,
                fontweight="bold", color="#555555")

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"架构图已生成: {output_path}")


def draw_flow(config: dict, output_path: str):
    """线性流程图（步骤→步骤→步骤）"""
    chinese_font = setup_chinese_fonts()

    steps = config["steps"]
    title = config.get("title", "流程图")
    figsize = tuple(config.get("figsize", [16, 5]))
    dpi = config.get("dpi", DEFAULT_DPI)
    direction = config.get("direction", "left-right")

    n_steps = len(steps)

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    if direction == "left-right":
        box_w = 1.8
        box_h = 1.2
        gap = 0.8
        total_w = n_steps * box_w + (n_steps - 1) * gap
        start_x = (figsize[0] - total_w) / 2

        ax.set_xlim(0, figsize[0])
        ax.set_ylim(0, figsize[1])

        # 标题
        ax.text(figsize[0] / 2, figsize[1] - 0.5, title,
                ha="center", va="center", fontsize=16, fontweight="bold")

        y_center = figsize[1] / 2 - 0.2

        for i, step in enumerate(steps):
            x = start_x + i * (box_w + gap)
            color = step.get("color") or get_phase_color(i)

            # 步骤编号圆圈
            circle = plt.Circle((x + box_w / 2, y_center + box_h / 2 + 0.35),
                               0.25, color=color, zorder=3)
            ax.add_patch(circle)
            ax.text(x + box_w / 2, y_center + box_h / 2 + 0.35,
                    str(i + 1), ha="center", va="center",
                    fontsize=12, fontweight="bold", color="white", zorder=4)

            # 步骤框
            rect = FancyBboxPatch(
                (x, y_center - box_h / 2), box_w, box_h,
                boxstyle="round,pad=0.1",
                facecolor=color, alpha=0.15,
                edgecolor=color, linewidth=1.5,
            )
            ax.add_patch(rect)

            # 步骤标题
            ax.text(x + box_w / 2, y_center + 0.15,
                    step["name"], ha="center", va="center",
                    fontsize=10, fontweight="bold", color="#333333")

            # 步骤描述
            desc = step.get("desc", "")
            if desc:
                ax.text(x + box_w / 2, y_center - 0.2,
                        desc, ha="center", va="center",
                        fontsize=8, color="#666666",
                        wrap=True)

            # 箭头
            if i < n_steps - 1:
                ax.annotate(
                    "", xy=(x + box_w + gap - 0.1, y_center),
                    xytext=(x + box_w + 0.1, y_center),
                    arrowprops=dict(
                        arrowstyle="-|>", color="#888888",
                        lw=2, mutation_scale=18,
                    ),
                )

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"流程图已生成: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="数据驱动的流程/架构图生成（JSON → PNG）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s flow_config.json -o 技术路线.png
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

    output = args.output or str(config_path.parent / "flow.png")
    show_info(f"读取配置: {config_path}")

    chart_type = config.get("type", "layers")
    if chart_type == "layers":
        draw_layers(config, output)
    elif chart_type == "flow":
        draw_flow(config, output)
    else:
        show_error(f"不支持的图表类型: {chart_type}（可选: layers/flow）")
        sys.exit(1)


if __name__ == "__main__":
    main()
