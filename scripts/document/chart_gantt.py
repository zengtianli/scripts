#!/usr/bin/env python3
"""
数据驱动的甘特图生成脚本

输入 JSON 配置文件，输出 PNG 甘特图。
支持阶段条、里程碑菱形、子任务细条、验收节点标注。

JSON 配置格式见 --example 输出。
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
# 同目录公共模块
from chart_common import (
    BG_COLOR,
    CHART_AUTHOR,
    CHART_UPDATED,
    CHART_VERSION,
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

SCRIPT_NAME = "chart_gantt"

# ── 示例配置 ──────────────────────────────────────────────────

EXAMPLE_CONFIG = """{
  "title": "项目总体进度甘特图",
  "subtitle": "总工期约8个月（2026年4月—12月）",
  "phases": [
    {
      "name": "阶段一：项目启动与数据归集治理",
      "short": "启动+数据归集",
      "start": "2026-04-15",
      "end": "2026-06-30",
      "color": null
    },
    {
      "name": "阶段二：核算+水库管理",
      "short": "核算+水库管理",
      "start": "2026-05-15",
      "end": "2026-09-30",
      "color": null
    }
  ],
  "milestones": [
    {
      "name": "M0 合同签订",
      "date": "2026-04-15",
      "label": "50%启动款"
    }
  ],
  "figsize": [16, 8],
  "dpi": 300
}"""


# ── 核心绘图 ──────────────────────────────────────────────────


def parse_date(s: str) -> datetime:
    """解析日期字符串，支持 YYYY-MM-DD 和 YYYY-MM"""
    for fmt in ("%Y-%m-%d", "%Y-%m"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {s}")


def draw_gantt(config: dict, output_path: str):
    """根据配置绘制甘特图"""
    chinese_font = setup_chinese_fonts()

    phases = config.get("phases", [])
    milestones = config.get("milestones", [])
    title = config.get("title", "项目进度甘特图")
    subtitle = config.get("subtitle", "")
    figsize = tuple(config.get("figsize", [16, 8]))
    dpi = config.get("dpi", DEFAULT_DPI)

    if not phases:
        show_error("配置中没有 phases 数据")
        sys.exit(1)

    # 解析日期
    for i, p in enumerate(phases):
        p["_start"] = parse_date(p["start"])
        p["_end"] = parse_date(p["end"])
        p["_color"] = p.get("color") or get_phase_color(i)
        p["_duration"] = (p["_end"] - p["_start"]).days

    for m in milestones:
        m["_date"] = parse_date(m["date"])

    # 计算时间范围
    all_dates = [p["_start"] for p in phases] + [p["_end"] for p in phases]
    if milestones:
        all_dates += [m["_date"] for m in milestones]
    date_min = min(all_dates) - timedelta(days=7)
    date_max = max(all_dates) + timedelta(days=7)

    # ── 绘图 ──
    fig, ax = plt.subplots(figsize=figsize)
    fig.set_facecolor("white")
    ax.set_facecolor(BG_COLOR)

    n_phases = len(phases)
    bar_height = 0.6
    y_positions = list(range(n_phases))

    # 绘制阶段条
    for i, p in enumerate(phases):
        ax.barh(
            i,
            p["_duration"],
            left=p["_start"],
            height=bar_height,
            color=p["_color"],
            alpha=0.85,
            edgecolor="#333333",
            linewidth=0.8,
            zorder=2,
        )
        # 条内文字：短名称 + 日期范围
        short = p.get("short", p["name"])
        date_range = f"{p['_start'].strftime('%m.%d')}—{p['_end'].strftime('%m.%d')}"
        mid = p["_start"] + timedelta(days=p["_duration"] / 2)

        if p["_duration"] > 30:
            ax.text(
                mid,
                i,
                f"{short}\n{date_range}",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color="white",
                zorder=3,
            )
        else:
            # 短条：文字放在右侧
            ax.text(
                p["_end"] + timedelta(days=2),
                i,
                f"{short} ({date_range})",
                ha="left",
                va="center",
                fontsize=8,
                color="#333333",
                zorder=3,
            )

    # 绘制里程碑
    for m in milestones:
        # 找到最近的阶段 y 位置
        y = -0.8  # 放在最上方
        ax.scatter(
            m["_date"],
            y,
            marker="D",
            s=120,
            color=MILESTONE_COLOR,
            edgecolor=MILESTONE_EDGE,
            linewidth=1.5,
            zorder=4,
        )
        label_text = m["name"]
        if m.get("label"):
            label_text += f"\n({m['label']})"
        ax.annotate(
            label_text,
            (m["_date"], y),
            textcoords="offset points",
            xytext=(0, -18),
            ha="center",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            color="#333333",
        )
        # 竖虚线
        ax.axvline(m["_date"], color=MILESTONE_COLOR, linestyle="--", alpha=0.3, linewidth=0.8, zorder=1)

    # ── 坐标轴 ──
    ax.set_yticks(y_positions)
    ax.set_yticklabels(
        [p.get("short", p["name"]) for p in phases],
        fontsize=11,
        fontweight="bold",
    )
    ax.invert_yaxis()

    # 扩展 y 范围以容纳里程碑
    if milestones:
        ax.set_ylim(n_phases - 0.5, -1.5)
    else:
        ax.set_ylim(n_phases - 0.5, -0.5)

    # X 轴月度刻度
    ax.set_xlim(date_min, date_max)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y年%m月"))
    ax.xaxis.set_minor_locator(mdates.WeekdayLocator(byweekday=0))
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=10)

    # 网格
    ax.grid(True, axis="x", which="major", color=GRID_COLOR, linestyle="-", linewidth=0.8, alpha=0.7)
    ax.grid(True, axis="x", which="minor", color=GRID_COLOR, linestyle=":", linewidth=0.4, alpha=0.5)
    ax.grid(False, axis="y")

    # 标题
    if subtitle:
        ax.set_title(f"{title}\n{subtitle}", fontsize=16, fontweight="bold", pad=15)
    else:
        ax.set_title(title, fontsize=16, fontweight="bold", pad=15)

    # 图例
    legend_patches = [mpatches.Patch(color=p["_color"], label=p.get("short", p["name"])) for p in phases]
    if milestones:
        legend_patches.append(
            plt.scatter([], [], marker="D", s=80, color=MILESTONE_COLOR, edgecolor=MILESTONE_EDGE, label="里程碑")
        )
    ax.legend(handles=legend_patches, loc="upper right", fontsize=9, framealpha=0.9)

    # 边框
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)

    plt.tight_layout()
    save_figure(fig, output_path, dpi)
    show_success(f"甘特图已生成: {output_path}")


# ── CLI ───────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="数据驱动的甘特图生成（JSON → PNG）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  %(prog)s gantt_config.json -o 甘特图.png
  %(prog)s gantt_config.json                    输出到同目录 gantt.png
  %(prog)s --example                            打印示例 JSON 配置
""",
    )
    parser.add_argument("config", nargs="?", help="JSON 配置文件路径")
    parser.add_argument("-o", "--output", help="输出 PNG 路径（默认: 配置文件同目录/gantt.png）")
    parser.add_argument("--example", action="store_true", help="打印示例 JSON 配置")
    parser.add_argument("--version", action="store_true", help="显示版本信息")

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

    with open(config_path, encoding="utf-8") as f:
        config = json.load(f)

    output = args.output or str(config_path.parent / "gantt.png")
    show_info(f"读取配置: {config_path}")
    draw_gantt(config, output)


if __name__ == "__main__":
    main()
