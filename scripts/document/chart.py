#!/usr/bin/env python3
"""
数据驱动的图表生成统一工具（JSON → PNG）

用法: python3 chart.py <子命令> <config.json> [-o output.png] [--example]

子命令:
  bar     条形/柱状统计图（horizontal/vertical/grouped）
  gantt   甘特图（阶段条 + 里程碑）
  flow    流程框图 / 分层架构图（layers/flow）

版本: 3.0.0
作者: tianli
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from chart_common import (
    BG_COLOR,
    CHART_AUTHOR,
    CHART_UPDATED,
    DEFAULT_DPI,
    GRID_COLOR,
    MILESTONE_COLOR,
    MILESTONE_EDGE,
    get_phase_color,
    save_figure,
    setup_chinese_fonts,
)
from display import show_error, show_info, show_success
from file_ops import show_version_info

SCRIPT_VERSION = "3.0.0"

# ── 示例配置 ─────────────────────────────────────────────────

EXAMPLES = {
    "bar": """{
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
  ]
}""",
    "gantt": """{
  "title": "项目总体进度甘特图",
  "subtitle": "总工期约8个月（2026年4月—12月）",
  "phases": [
    {"name": "阶段一：项目启动", "short": "启动", "start": "2026-04-15", "end": "2026-06-30"},
    {"name": "阶段二：核算开发", "short": "核算", "start": "2026-05-15", "end": "2026-09-30"}
  ],
  "milestones": [{"name": "M0 合同签订", "date": "2026-04-15", "label": "50%启动款"}]
}""",
    "flow": """{
  "title": "项目总体技术路线图",
  "type": "layers",
  "layers": [
    {"name": "第一层：基础层", "boxes": [{"text": "数据源A"}, {"text": "数据源B"}], "output": "清洗后数据"},
    {"name": "第二层：核算层", "boxes": [{"text": "核算方法"}, {"text": "水量平衡"}], "output": "核算成果"}
  ]
}""",
}


# ── Bar 绘图函数 ──────────────────────────────────────────────


def draw_horizontal_bar(config: dict, output_path: str):
    setup_chinese_fonts()
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
    bars = ax.barh(y_pos, values, height=0.55, color=colors, edgecolor="#333333", linewidth=0.8, alpha=0.9)

    max_val = max(values)
    for i, (_bar, val) in enumerate(zip(bars, values)):
        pct = percents[i]
        label_text = f"{val} {unit}（{pct}%）" if pct is not None else f"{val} {unit}"
        if val > max_val * 0.3:
            ax.text(val / 2, i, label_text, ha="center", va="center", fontsize=10, fontweight="bold", color="white")
        else:
            ax.text(val + max_val * 0.01, i, label_text, ha="left", va="center", fontsize=9, color="#333333")

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.set_xlabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    if show_total:
        total_val = sum(values)
        total_label = config.get("total_label", "合计")
        ax.text(
            0.98, 0.02, f"{total_label}：{total_val:.2f} {unit}",
            transform=ax.transAxes, ha="right", va="bottom", fontsize=11, fontweight="bold", color="#666666",
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC", alpha=0.9),
        )

    ax.grid(True, axis="x", color=GRID_COLOR, linestyle="-", linewidth=0.6, alpha=0.7)
    ax.grid(False, axis="y")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"条形图已生成: {output_path}")


def draw_vertical_bar(config: dict, output_path: str):
    setup_chinese_fonts()
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
    bars = ax.bar(x_pos, values, width=0.55, color=colors, edgecolor="#333333", linewidth=0.8, alpha=0.9)

    for bar, val in zip(bars, values):
        pct_item = next((it for it in items if it["value"] == val), None)
        pct = pct_item.get("percent") if pct_item else None
        text = f"{val}\n({pct}%)" if pct is not None else f"{val}"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), text,
                ha="center", va="bottom", fontsize=9, fontweight="bold", color="#333333")

    ax.set_xticks(x_pos)
    ax.set_xticklabels(labels, fontsize=10, fontweight="bold")
    ax.set_ylabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.grid(True, axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.6, alpha=0.7)
    ax.grid(False, axis="x")
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"柱状图已生成: {output_path}")


def draw_grouped_bar(config: dict, output_path: str):
    setup_chinese_fonts()
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
        bars = ax.bar(x + offset, s["values"], bar_width * 0.9, label=s["name"],
                      color=color, edgecolor="#333333", linewidth=0.6, alpha=0.9)
        for bar, val in zip(bars, s["values"]):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), f"{val}", ha="center", va="bottom", fontsize=8)

    ax.set_xticks(x)
    ax.set_xticklabels(groups, fontsize=10, fontweight="bold")
    ax.set_ylabel(unit, fontsize=11)
    ax.set_title(title, fontsize=16, fontweight="bold", pad=15)
    ax.legend(fontsize=10, framealpha=0.9)
    ax.grid(True, axis="y", color=GRID_COLOR, linestyle="-", linewidth=0.6, alpha=0.7)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"分组柱状图已生成: {output_path}")


# ── Gantt 绘图函数 ────────────────────────────────────────────


def _parse_date(s: str) -> datetime:
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {s}")


def draw_gantt(config: dict, output_path: str):
    setup_chinese_fonts()
    phases = config.get("phases", [])
    milestones = config.get("milestones", [])
    title = config.get("title", "项目进度甘特图")
    subtitle = config.get("subtitle", "")
    figsize = tuple(config.get("figsize", [16, 8]))
    dpi = config.get("dpi", DEFAULT_DPI)

    if not phases:
        show_error("配置中没有 phases 数据")
        sys.exit(1)

    for i, p in enumerate(phases):
        p["_start"] = _parse_date(p["start"])
        p["_end"] = _parse_date(p["end"])
        p["_color"] = p.get("color") or get_phase_color(i)
        p["_duration"] = (p["_end"] - p["_start"]).days
    for m in milestones:
        m["_date"] = _parse_date(m["date"])

    all_dates = [p["_start"] for p in phases] + [p["_end"] for p in phases]
    if milestones:
        all_dates += [m["_date"] for m in milestones]
    date_min = min(all_dates) - timedelta(days=7)
    date_max = max(all_dates) + timedelta(days=7)

    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    n_phases = len(phases)
    bar_height = 0.6

    for i, p in enumerate(phases):
        ax.barh(i, p["_duration"], left=p["_start"], height=bar_height, color=p["_color"],
                alpha=0.85, edgecolor="#333333", linewidth=0.8, zorder=2)
        short = p.get("short", p["name"])
        date_range = f"{p['_start'].strftime('%m.%d')}—{p['_end'].strftime('%m.%d')}"
        mid = p["_start"] + timedelta(days=p["_duration"] / 2)
        if p["_duration"] > 30:
            ax.text(mid, i, f"{short}\n{date_range}", ha="center", va="center",
                    fontsize=9, fontweight="bold", color="white", zorder=3)
        else:
            ax.text(p["_end"] + timedelta(days=2), i, f"{short} ({date_range})",
                    ha="left", va="center", fontsize=8, color="#333333", zorder=3)

    for m in milestones:
        y = -0.8
        ax.scatter(m["_date"], y, marker="D", s=120, color=MILESTONE_COLOR,
                   edgecolor=MILESTONE_EDGE, linewidth=1.5, zorder=4)
        label_text = m["name"]
        if m.get("label"):
            label_text += f"\n({m['label']})"
        ax.annotate(label_text, (m["_date"], y), textcoords="offset points", xytext=(0, -18),
                    ha="center", va="top", fontsize=7.5, fontweight="bold", color="#333333")
        ax.axvline(m["_date"], color=MILESTONE_COLOR, linestyle="--", alpha=0.3, linewidth=0.8, zorder=1)

    ax.set_yticks(range(n_phases))
    ax.set_yticklabels([p.get("short", p["name"]) for p in phases], fontsize=11, fontweight="bold")
    ax.invert_yaxis()
    ax.set_ylim(n_phases - 0.5, -1.5 if milestones else -0.5)
    ax.set_xlim(date_min, date_max)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y年%m月"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=10)

    ax.grid(True, axis="x", which="major", color=GRID_COLOR, linestyle="-", linewidth=0.8, alpha=0.7)
    ax.grid(True, axis="x", which="minor", color=GRID_COLOR, linestyle=":", linewidth=0.4, alpha=0.5)
    ax.grid(False, axis="y")

    title_text = f"{title}\n{subtitle}" if subtitle else title
    ax.set_title(title_text, fontsize=16, fontweight="bold", pad=15)

    legend_patches = [mpatches.Patch(color=p["_color"], label=p.get("short", p["name"])) for p in phases]
    if milestones:
        legend_patches.append(
            plt.scatter([], [], marker="D", s=80, color=MILESTONE_COLOR, edgecolor=MILESTONE_EDGE, label="里程碑"))
    ax.legend(handles=legend_patches, loc="upper right", fontsize=9, framealpha=0.9)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"甘特图已生成: {output_path}")


# ── Flow 绘图函数 ─────────────────────────────────────────────


def draw_layers(config: dict, output_path: str):
    setup_chinese_fonts()
    layers = config["layers"]
    title = config.get("title", "架构图")
    figsize = tuple(config.get("figsize", [14, 12]))
    dpi = config.get("dpi", DEFAULT_DPI)
    bottom_bar = config.get("bottom_bar")

    n_layers = len(layers)
    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor("white")

    layer_height = 1.0
    layer_gap = 0.5
    total_height = n_layers * layer_height + (n_layers - 1) * layer_gap
    if bottom_bar:
        total_height += layer_height + layer_gap

    canvas_width = 10.0
    margin_x = 0.5
    box_margin = 0.3

    ax.set_xlim(-margin_x, canvas_width + margin_x)
    ax.set_ylim(-0.5, total_height + 1.0)
    ax.set_aspect("equal")
    ax.axis("off")

    ax.text(canvas_width / 2, total_height + 0.6, title, ha="center", va="center", fontsize=16, fontweight="bold")

    for layer_idx, layer in enumerate(layers):
        y_top = total_height - layer_idx * (layer_height + layer_gap)
        y_bottom = y_top - layer_height
        y_center = (y_top + y_bottom) / 2
        color = layer.get("color") or get_phase_color(layer_idx)

        layer_bg = FancyBboxPatch((0, y_bottom), canvas_width, layer_height,
                                  boxstyle="round,pad=0.05", facecolor=color, alpha=0.12,
                                  edgecolor=color, linewidth=1.5)
        ax.add_patch(layer_bg)
        ax.text(0.2, y_top - 0.12, layer["name"], ha="left", va="top", fontsize=10, fontweight="bold", color=color)

        boxes = layer.get("boxes", [])
        if boxes:
            n_boxes = len(boxes)
            box_width = (canvas_width - box_margin * (n_boxes + 1)) / n_boxes
            box_h = 0.5
            box_y = y_center - box_h / 2 - 0.05
            for bi, box in enumerate(boxes):
                box_x = box_margin + bi * (box_width + box_margin)
                box_color = box.get("color", color)
                rect = FancyBboxPatch((box_x, box_y), box_width, box_h,
                                      boxstyle="round,pad=0.08", facecolor="white",
                                      edgecolor=box_color, linewidth=1.2)
                ax.add_patch(rect)
                ax.text(box_x + box_width / 2, box_y + box_h / 2, box["text"],
                        ha="center", va="center", fontsize=9, fontweight="bold", color="#333333")

        output_text = layer.get("output")
        if output_text:
            ax.text(canvas_width - 0.2, y_bottom + 0.08, f"→ {output_text}",
                    ha="right", va="bottom", fontsize=8, fontstyle="italic", color="#666666")

        if layer_idx < n_layers - 1:
            arrow_y_start = y_bottom - 0.05
            arrow_y_end = y_bottom - layer_gap + 0.05
            ax.annotate("", xy=(canvas_width / 2, arrow_y_end), xytext=(canvas_width / 2, arrow_y_start),
                        arrowprops=dict(arrowstyle="-|>", color="#666666", lw=2, mutation_scale=20))

    if bottom_bar:
        bar_y = -0.3
        bar_h = 0.6
        bar_bg = FancyBboxPatch((0, bar_y), canvas_width, bar_h, boxstyle="round,pad=0.05",
                                facecolor="#555555", alpha=0.15, edgecolor="#555555", linewidth=1.5)
        ax.add_patch(bar_bg)
        ax.text(canvas_width / 2, bar_y + bar_h / 2, bottom_bar,
                ha="center", va="center", fontsize=10, fontweight="bold", color="#555555")

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"架构图已生成: {output_path}")


def draw_flow(config: dict, output_path: str):
    setup_chinese_fonts()
    steps = config["steps"]
    title = config.get("title", "流程图")
    figsize = tuple(config.get("figsize", [16, 5]))
    dpi = config.get("dpi", DEFAULT_DPI)

    n_steps = len(steps)
    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor("white")
    ax.axis("off")

    box_w = 1.8
    box_h = 1.2
    gap = 0.8
    total_w = n_steps * box_w + (n_steps - 1) * gap
    start_x = (figsize[0] - total_w) / 2

    ax.set_xlim(0, figsize[0])
    ax.set_ylim(0, figsize[1])
    ax.text(figsize[0] / 2, figsize[1] - 0.5, title, ha="center", va="center", fontsize=16, fontweight="bold")

    y_center = figsize[1] / 2 - 0.2

    for i, step in enumerate(steps):
        x = start_x + i * (box_w + gap)
        color = step.get("color") or get_phase_color(i)

        circle = plt.Circle((x + box_w / 2, y_center + box_h / 2 + 0.35), 0.25, color=color, zorder=3)
        ax.add_patch(circle)
        ax.text(x + box_w / 2, y_center + box_h / 2 + 0.35, str(i + 1),
                ha="center", va="center", fontsize=12, fontweight="bold", color="white", zorder=4)

        rect = FancyBboxPatch((x, y_center - box_h / 2), box_w, box_h, boxstyle="round,pad=0.1",
                              facecolor=color, alpha=0.15, edgecolor=color, linewidth=1.5)
        ax.add_patch(rect)
        ax.text(x + box_w / 2, y_center + 0.15, step["name"],
                ha="center", va="center", fontsize=10, fontweight="bold", color="#333333")

        desc = step.get("desc", "")
        if desc:
            ax.text(x + box_w / 2, y_center - 0.2, desc,
                    ha="center", va="center", fontsize=8, color="#666666", wrap=True)

        if i < n_steps - 1:
            ax.annotate("", xy=(x + box_w + gap - 0.1, y_center), xytext=(x + box_w + 0.1, y_center),
                        arrowprops=dict(arrowstyle="-|>", color="#888888", lw=2, mutation_scale=18))

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"流程图已生成: {output_path}")


# ── 子命令路由 ────────────────────────────────────────────────

CHART_TYPES = {
    "bar": {"default_output": "bar.png", "draw": {
        "horizontal": draw_horizontal_bar, "vertical": draw_vertical_bar, "grouped": draw_grouped_bar,
    }},
    "gantt": {"default_output": "gantt.png", "draw": draw_gantt},
    "flow": {"default_output": "flow.png", "draw": {
        "layers": draw_layers, "flow": draw_flow,
    }},
}


def main():
    parser = argparse.ArgumentParser(
        description="数据驱动的图表生成统一工具（JSON → PNG）",
        usage="python3 chart.py <bar|gantt|flow> <config.json> [-o output.png] [--example]",
        add_help=False,
    )
    parser.add_argument("command", nargs="?", help="图表类型: bar, gantt, flow")
    parser.add_argument("config", nargs="?", help="JSON 配置文件")
    parser.add_argument("-o", "--output", help="输出 PNG 路径")
    parser.add_argument("--example", action="store_true", help="打印示例配置")
    parser.add_argument("--version", action="store_true", help="版本信息")
    parser.add_argument("-h", "--help", action="store_true")
    args, _ = parser.parse_known_args()

    if args.version:
        show_version_info(SCRIPT_VERSION, CHART_AUTHOR, CHART_UPDATED)
        return

    if args.help or not args.command:
        print(__doc__)
        return

    cmd = args.command
    if cmd not in CHART_TYPES:
        show_error(f"未知子命令: {cmd}（可选: bar, gantt, flow）")
        sys.exit(1)

    if args.example:
        print(EXAMPLES.get(cmd, "无示例"))
        return

    if not args.config:
        show_error("请提供 JSON 配置文件")
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        show_error(f"配置文件不存在: {config_path}")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    ct = CHART_TYPES[cmd]
    output = args.output or str(config_path.parent / ct["default_output"])
    show_info(f"读取配置: {config_path}")

    draw = ct["draw"]
    if isinstance(draw, dict):
        chart_type = config.get("type", list(draw.keys())[0])
        if chart_type not in draw:
            show_error(f"不支持的类型: {chart_type}（可选: {', '.join(draw.keys())}）")
            sys.exit(1)
        draw[chart_type](config, output)
    else:
        draw(config, output)


if __name__ == "__main__":
    main()
