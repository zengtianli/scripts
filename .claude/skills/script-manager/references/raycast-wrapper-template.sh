#!/bin/bash
# ============================================================
# Raycast Wrapper Template
# ============================================================

# @raycast.schemaVersion 1
# @raycast.title {脚本标题}
# @raycast.description {脚本功能描述}
# @raycast.mode {silent|compact|fullOutput}
# @raycast.icon {emoji}
# @raycast.packageName {分类名称}

# ============================================================
# 可选参数配置
# ============================================================

# 文本参数示例
# @raycast.argument1 { "type": "text", "placeholder": "输入提示" }

# 下拉选择示例
# @raycast.argument1 { "type": "dropdown", "placeholder": "选择选项", "data": [{"title": "选项1", "value": "value1"}, {"title": "选项2", "value": "value2"}] }

# ============================================================
# 调用实际脚本
# ============================================================

# Python 脚本调用
source "$(dirname "$0")/../lib/run_python.sh" && run_python "{category}/{script_name}.py" "$@"

# Shell 脚本调用
# source "$(dirname "$0")/../lib/run_python.sh" && run_shell "{category}/{script_name}.sh" "$@"

# Streamlit 项目调用
# source "$(dirname "$0")/../lib/run_python.sh" && run_streamlit "{project_name}" "app.py" "$@"
