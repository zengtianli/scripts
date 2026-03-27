#!/usr/bin/env python3
"""
水利工具集 Portal — 自动发现并展示所有水利计算工具
"""

import sys
from pathlib import Path

# 添加 lib 到路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "lib"))

import yaml
import streamlit as st
from hydraulic.st_utils import page_config, footer

# ============================================================
# 页面配置
# ============================================================
page_config("水利工具集", "🧰")

# ============================================================
# 常量
# ============================================================
PROJECTS_DIR = Path(__file__).resolve().parent.parent
SELF_NAME = "hydro_toolkit"

STATUS_BADGE = {
    "active": ("🟢", "可用"),
    "dev": ("🟡", "开发中"),
    "data": ("🔵", "数据集"),
}

VALID_TYPES = {"hydraulic", "streamlit"}


# ============================================================
# 工具函数
# ============================================================
def discover_projects():
    """扫描 projects/*/_project.yaml，返回水利相关项目列表。"""
    projects = []
    for yaml_path in sorted(PROJECTS_DIR.glob("*/_project.yaml")):
        proj_dir = yaml_path.parent
        if proj_dir.name == SELF_NAME:
            continue
        try:
            meta = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not meta or meta.get("type") not in VALID_TYPES:
            continue

        # 兼容 entry 格式：字符串 or 字典
        entry = meta.get("entry", {})
        if isinstance(entry, str):
            web_entry = entry
            cli_entry = None
        elif isinstance(entry, dict):
            web_entry = entry.get("web")
            cli_entry = entry.get("cli")
        else:
            web_entry = None
            cli_entry = None

        projects.append({
            "name": meta.get("name", proj_dir.name),
            "title": meta.get("title", proj_dir.name),
            "description": meta.get("description", ""),
            "icon": meta.get("icon", "🌊"),
            "status": meta.get("status", "active"),
            "tags": meta.get("tags", []),
            "dir": proj_dir.name,
            "web_entry": web_entry,
            "cli_entry": cli_entry,
        })
    return projects


def get_launch_cmd(proj):
    """生成 Streamlit 启动命令。"""
    if not proj["web_entry"]:
        return None
    entry = proj["web_entry"]
    dir_name = proj["dir"]
    return f"cd ~/Dev/scripts && streamlit run projects/{dir_name}/{entry}"


# ============================================================
# 页面内容
# ============================================================
st.title("🧰 水利工具集")
st.caption("浙水设计 · 水利计算工具门户")

projects = discover_projects()

# ============================================================
# 侧边栏 — 筛选
# ============================================================
with st.sidebar:
    st.header("📋 筛选")

    status_options = ["全部"] + sorted({p["status"] for p in projects})
    selected_status = st.selectbox("状态", status_options)

    all_tags = sorted({t for p in projects for t in p["tags"]})
    selected_tags = st.multiselect("标签", all_tags)

    st.divider()
    st.metric("工具总数", len(projects))
    for s, (dot, label) in STATUS_BADGE.items():
        count = sum(1 for p in projects if p["status"] == s)
        if count:
            st.caption(f"{dot} {label}：{count} 个")

# 过滤
filtered = projects
if selected_status != "全部":
    filtered = [p for p in filtered if p["status"] == selected_status]
if selected_tags:
    filtered = [p for p in filtered if set(selected_tags) & set(p["tags"])]

# ============================================================
# 工具卡片
# ============================================================
if not filtered:
    st.info("没有匹配的工具")
else:
    # 按状态排序：active → dev → data
    order = {"active": 0, "dev": 1, "data": 2}
    filtered.sort(key=lambda p: (order.get(p["status"], 9), p["title"]))

    # 两列布局
    for i in range(0, len(filtered), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx >= len(filtered):
                break
            proj = filtered[idx]
            dot, status_label = STATUS_BADGE.get(proj["status"], ("⚪", "未知"))

            with col:
                with st.container(border=True):
                    st.subheader(f"{proj['icon']} {proj['title']}")
                    st.caption(f"{dot} {status_label}")
                    st.write(proj["description"])

                    # 标签
                    if proj["tags"]:
                        st.markdown(
                            " ".join(f"`{t}`" for t in proj["tags"]),
                        )

                    # 启动方式
                    cmd = get_launch_cmd(proj)
                    if cmd:
                        st.code(cmd, language="bash")
                    elif proj["cli_entry"]:
                        st.code(
                            f"cd ~/Dev/scripts/projects/{proj['dir']}\n"
                            f"python3 {proj['cli_entry']}",
                            language="bash",
                        )
                    else:
                        st.info(f"数据目录：`projects/{proj['dir']}/`")

# ============================================================
# 页脚
# ============================================================
footer("水利工具集 · 浙水设计")
