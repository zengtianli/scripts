#!/usr/bin/env python3
"""
通用函数库 - 统一导出入口

使用方式（sys.path 已指向 lib/）：
    from display import show_success
    from finder import get_input_files

或通过包导入：
    from lib import show_success, get_input_files
"""

__version__ = "3.0.0"

# === display ===
from display import (
    show_success,
    show_error,
    show_warning,
    show_info,
    show_processing,
    show_progress,
)

# === finder ===
from finder import (
    get_finder_selection,
    get_finder_selection_single,
    get_finder_current_dir,
    get_input_files,
    require_single_file,
)

# === clipboard ===
from clipboard import (
    copy_to_clipboard,
    get_from_clipboard,
    get_clipboard_files,
    paste_files,
)

# === progress ===
from progress import ProgressTracker

# === usage_log ===
from usage_log import log_usage

# === file_ops ===
from file_ops import (
    check_file_extension,
    check_file_exists,
    validate_input_file,
    find_files_by_extension,
    ensure_directory,
    check_command_exists,
    fatal_error,
    get_file_basename,
    check_python_packages,
    show_version_info,
    show_help_header,
    show_help_footer,
    add_prefix,
    move_up,
    flatten_dir,
    organize_by_type,
    create_folder,
)

# === env ===
from env import PROJECT_ROOT, PYTHON_PATH, USAGE_LOG

# === 兼容别名（过渡期）===
# 允许 `import common_utils` 继续工作（通过 __init__.py re-export）
