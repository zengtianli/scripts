#!/Users/tianli/miniforge3/bin/python3
"""
通用工具函数库
提供所有脚本共用的工具函数
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Union

# ===== 常量 =====
PYTHON_PATH = "/Users/tianli/miniforge3/bin/python3"
MINIFORGE_BIN = "/Users/tianli/miniforge3/bin"
EXECUTE_DIR = "/Users/tianli/useful_scripts/execute"
SCRIPTS_BASE = f"{EXECUTE_DIR}/scripts"
TOOLS_DIR = f"{EXECUTE_DIR}/tools"
USAGE_LOG = os.path.expanduser("~/.useful_scripts_usage.log")


# ===== 消息显示函数 =====

def show_success(msg: str):
    """显示成功消息"""
    print(f"✅ {msg}")


def show_error(msg: str):
    """显示错误消息"""
    print(f"❌ {msg}")


def show_warning(msg: str):
    """显示警告消息"""
    print(f"⚠️ {msg}")


def show_info(msg: str):
    """显示信息消息"""
    print(f"ℹ️ {msg}")


def show_processing(msg: str):
    """显示处理中消息"""
    print(f"🔄 {msg}")


def show_progress(current: int, total: int, item: str = ""):
    """显示进度"""
    percentage = (current * 100) // total if total > 0 else 0
    print(f"🔄 进度: {percentage}% ({current}/{total}) {item}")


def show_version_info(name: str, version: str, author: str = "", updated: str = ""):
    """显示版本信息"""
    print(f"📦 {name} v{version}")
    if author:
        print(f"👤 作者: {author}")
    if updated:
        print(f"📅 更新: {updated}")


def show_help_header(title: str, description: str = ""):
    """显示帮助信息头"""
    print(f"\n{'='*60}")
    print(f"📖 {title}")
    if description:
        print(f"   {description}")
    print(f"{'='*60}\n")


def show_help_footer():
    """显示帮助信息尾"""
    print(f"\n{'='*60}\n")


def fatal_error(message: str):
    """致命错误 - 立即退出"""
    show_error(message)
    sys.exit(1)


# ===== 文件操作函数 =====

def check_file_extension(filepath: str, expected_ext: str) -> bool:
    """检查文件扩展名"""
    actual_ext = Path(filepath).suffix.lower().lstrip('.')
    return actual_ext == expected_ext.lower().lstrip('.')


def check_file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filepath)


def validate_input_file(filepath: str, expected_ext: Optional[str] = None) -> bool:
    """验证输入文件"""
    if not check_file_exists(filepath):
        show_error(f"文件不存在: {filepath}")
        return False
    
    if expected_ext and not check_file_extension(filepath, expected_ext):
        show_error(f"请选择 .{expected_ext} 文件")
        return False
    
    return True


def find_files_by_extension(
    paths: Union[str, Path, List[Union[str, Path]]],
    extensions: Union[str, List[str]],
    recursive: bool = False
) -> List[Path]:
    """根据扩展名查找文件"""
    if isinstance(paths, (str, Path)):
        paths = [paths]
    if isinstance(extensions, str):
        extensions = [extensions]
    
    all_files = []
    
    for path in paths:
        path = Path(path)
        
        if path.is_file():
            ext = path.suffix.lower().lstrip('.')
            if ext in [e.lower().lstrip('.') for e in extensions]:
                all_files.append(path)
            continue
        
        if path.is_dir():
            for extension in extensions:
                extension = extension.lower().lstrip('.')
                pattern = f"**/*.{extension}" if recursive else f"*.{extension}"
                all_files.extend(path.glob(pattern))
    
    return sorted(set(all_files))


def ensure_directory(dir_path: Union[str, Path]) -> bool:
    """确保目录存在"""
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        show_error(f"无法创建目录: {dir_path} - {e}")
        return False


def get_file_basename(filepath: str) -> str:
    """获取文件名（不含扩展名）"""
    return Path(filepath).stem


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def check_python_packages(*packages: str) -> bool:
    """检查 Python 包是否已安装"""
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        show_error(f"缺少依赖包: {', '.join(missing)}")
        show_info(f"请运行: pip install {' '.join(missing)}")
        return False
    return True


# ===== 进度跟踪器 =====

class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total: int = 0):
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.total_count = 0
        self.current_count = 0
        self.total_expected = total
    
    def show(self, message: str = ""):
        """显示当前进度"""
        self.current_count += 1
        if self.total_expected > 0:
            percentage = (self.current_count * 100) // self.total_expected
            show_processing(f"进度: {percentage}% ({self.current_count}/{self.total_expected}) {message}")
        else:
            show_processing(f"处理中 ({self.current_count}): {message}")
    
    def add_success(self):
        """添加成功计数"""
        self.success_count += 1
        self.total_count += 1
    
    def add_failure(self):
        """添加失败计数"""
        self.failed_count += 1
        self.total_count += 1
    
    def add_skip(self):
        """添加跳过计数"""
        self.skipped_count += 1
        self.total_count += 1
    
    def show_summary(self, operation_name: str = "处理"):
        """显示统计摘要"""
        print()
        show_info(f"{operation_name}完成")
        print(f"✅ 成功: {self.success_count} 个")
        if self.failed_count > 0:
            print(f"❌ 失败: {self.failed_count} 个")
        if self.skipped_count > 0:
            print(f"⚠️ 跳过: {self.skipped_count} 个")
        print(f"📊 总计: {self.total_count} 个")
        
        if self.total_count > 0:
            success_rate = (self.success_count * 100) // self.total_count
            print(f"📊 成功率: {success_rate}%")


# ===== Finder 操作函数 =====

def get_finder_selection() -> List[str]:
    """获取 Finder 选中的文件列表"""
    script = '''
    tell application "Finder"
        set selectedItems to selection as list
        if (count of selectedItems) = 0 then
            return ""
        end if
        set posixPaths to {}
        repeat with i from 1 to count of selectedItems
            set end of posixPaths to POSIX path of (item i of selectedItems as alias)
        end repeat
        set AppleScript's text item delimiters to "\\n"
        set pathsText to posixPaths as text
        set AppleScript's text item delimiters to ""
        return pathsText
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        paths = result.stdout.strip()
        if not paths:
            return []
        return [p for p in paths.split('\n') if p]
    except Exception:
        return []


def get_finder_selection_single() -> Optional[str]:
    """获取 Finder 选中的单个文件"""
    files = get_finder_selection()
    if len(files) == 1:
        return files[0]
    return None


def get_finder_current_dir() -> Optional[str]:
    """获取 Finder 当前目录"""
    script = '''
    tell application "Finder"
        if (count of (selection as list)) > 0 then
            set firstItem to item 1 of (selection as list)
            if class of firstItem is folder then
                POSIX path of (firstItem as alias)
            else
                POSIX path of (container of firstItem as alias)
            end if
        else
            POSIX path of (insertion location as alias)
        end if
    end tell
    '''
    try:
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def get_input_files(
    args: List[str],
    expected_ext=None,
    allow_multiple: bool = True
) -> List[str]:
    """
    获取输入文件列表
    优先使用命令行参数，没有参数时从 Finder 获取
    """
    files = []
    
    if args:
        files = [a for a in args if not a.startswith('-')]
    else:
        files = get_finder_selection()
        if not files:
            show_error("请在 Finder 中选择文件，或通过命令行传入文件路径")
            return []
    
    allowed_exts = None
    if expected_ext:
        if isinstance(expected_ext, str):
            allowed_exts = [expected_ext.lower().lstrip('.')]
        else:
            allowed_exts = [e.lower().lstrip('.') for e in expected_ext]
    
    valid_files = []
    for f in files:
        if not os.path.exists(f):
            show_warning(f"文件不存在: {f}")
            continue
        
        if allowed_exts:
            ext = Path(f).suffix.lower().lstrip('.')
            if ext not in allowed_exts:
                show_warning(f"跳过非 .{'/'.join(allowed_exts)} 文件: {f}")
                continue
        
        valid_files.append(f)
    
    if not allow_multiple and len(valid_files) > 1:
        show_warning("只支持处理单个文件，将处理第一个")
        valid_files = valid_files[:1]
    
    return valid_files


# ===== 剪贴板操作 =====

def copy_to_clipboard(text: str):
    """复制文本到剪贴板"""
    process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
    process.communicate(text.encode('utf-8'))


def get_from_clipboard() -> str:
    """从剪贴板获取文本"""
    result = subprocess.run(['pbpaste'], capture_output=True, text=True)
    return result.stdout


