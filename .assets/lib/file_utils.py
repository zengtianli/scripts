#!/Users/tianli/miniforge3/bin/python3
"""
文件操作工具模块
"""

import os
import shutil
from pathlib import Path
from typing import List, Optional, Union

from display import show_error, show_warning


def check_file_extension(filepath: str, expected_ext: str) -> bool:
    """
    检查文件扩展名
    
    Args:
        filepath: 文件路径
        expected_ext: 期望的扩展名（不含点）
    
    Returns:
        是否匹配
    """
    actual_ext = Path(filepath).suffix.lower().lstrip('.')
    return actual_ext == expected_ext.lower().lstrip('.')


def check_file_exists(filepath: str) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filepath)


def validate_input_file(filepath: str, expected_ext: Optional[str] = None) -> bool:
    """
    验证输入文件
    
    Args:
        filepath: 文件路径
        expected_ext: 期望的扩展名（可选）
    
    Returns:
        是否有效
    """
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
    """
    根据扩展名查找文件
    
    Args:
        paths: 单个路径或路径列表
        extensions: 单个扩展名或扩展名列表
        recursive: 是否递归搜索
    
    Returns:
        找到的文件路径列表
    """
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


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def fatal_error(message: str):
    """致命错误 - 立即退出"""
    show_error(message)
    import sys
    sys.exit(1)


# ===== 应用启动 =====

def get_running_apps() -> set:
    """获取当前运行的应用列表"""
    import subprocess
    script = '''
    tell application "System Events"
        set runningApps to name of every application process whose background only is false
    end tell
    return runningApps
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    apps = set()
    for app in result.stdout.strip().split(', '):
        app = app.strip()
        if app:
            apps.add(app)
            apps.add(f"{app}.app")
    return apps


def launch_app(name: str) -> bool:
    """启动单个应用"""
    import subprocess
    app_name = name.replace('.app', '')
    result = subprocess.run(['open', '-a', app_name], capture_output=True)
    return result.returncode == 0


def launch_essential_apps(apps_file: Path) -> dict:
    """
    根据配置文件启动未运行的应用
    
    返回: {'running': [...], 'launched': [...], 'failed': [...]}
    """
    if not apps_file.exists():
        return {'error': f'文件不存在: {apps_file}'}
    
    # 读取配置
    apps = []
    for line in apps_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('==') and not line.startswith('-'):
            apps.append(line)
    
    # 获取运行中的应用
    running = get_running_apps()
    
    result = {'running': [], 'launched': [], 'failed': []}
    
    for app in apps:
        app_name = app.replace('.app', '')
        if app in running or app_name in running or f"{app_name}.app" in running:
            result['running'].append(app)
        else:
            if launch_app(app):
                result['launched'].append(app)
            else:
                result['failed'].append(app)
    
    return result


# ===== 剪贴板文件操作 =====

def get_clipboard_files() -> List[Path]:
    """获取剪贴板中的文件路径"""
    import subprocess
    script = '''
    tell application "System Events"
        try
            set theFiles to the clipboard as «class furl»
            set output to ""
            repeat with f in theFiles
                set output to output & (POSIX path of (f as text)) & linefeed
            end repeat
            return output
        on error
            try
                return POSIX path of (the clipboard as «class furl»)
            on error
                return ""
            end try
        end try
    end tell
    '''
    result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
    return [Path(p) for p in result.stdout.strip().split('\n') if p and Path(p).exists()]


def paste_files(target_dir: Union[str, Path]) -> List[Path]:
    """粘贴剪贴板文件到目标目录"""
    files = get_clipboard_files()
    pasted = []
    target = Path(target_dir)
    
    for src in files:
        dst = target / src.name
        # 处理同名
        if dst.exists():
            base, ext = dst.stem, dst.suffix
            counter = 1
            while dst.exists():
                dst = target / f"{base}_{counter}{ext}"
                counter += 1
        try:
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            pasted.append(dst)
        except Exception:
            pass
    return pasted


# ===== 文件批量操作 =====

def add_prefix(files: List[Path], prefix: str) -> List[tuple]:
    """批量添加文件名前缀，返回 [(旧名, 新名), ...]"""
    results = []
    for f in files:
        if not f.is_file():
            continue
        new_name = f.parent / f"{prefix}{f.name}"
        try:
            f.rename(new_name)
            results.append((f.name, new_name.name))
        except Exception:
            pass
    return results


def move_up(files: List[Path]) -> List[Path]:
    """将文件移动到上级目录"""
    moved = []
    for f in files:
        if not f.exists():
            continue
        parent = f.parent.parent
        if not parent.exists():
            continue
        dst = parent / f.name
        if dst.exists():
            continue
        try:
            shutil.move(str(f), str(dst))
            moved.append(dst)
        except Exception:
            pass
    return moved


def flatten_dir(dir_path: Union[str, Path]) -> List[Path]:
    """将子目录中的文件扁平化到当前目录"""
    root = Path(dir_path)
    moved = []
    for f in root.rglob('*'):
        if f.is_file() and f.parent != root:
            dst = root / f.name
            if dst.exists():
                base, ext = dst.stem, dst.suffix
                counter = 1
                while dst.exists():
                    dst = root / f"{base}_{counter}{ext}"
                    counter += 1
            try:
                shutil.move(str(f), str(dst))
                moved.append(dst)
            except Exception:
                pass
    # 删除空目录
    for d in sorted(root.rglob('*'), reverse=True):
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    return moved


def organize_by_type(files: List[Path], target_dir: Union[str, Path]) -> dict:
    """按文件类型整理到子目录"""
    TYPE_MAP = {
        'images': ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'ico'],
        'documents': ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md'],
        'videos': ['mp4', 'mov', 'avi', 'mkv', 'wmv'],
        'audio': ['mp3', 'wav', 'flac', 'aac', 'm4a'],
        'archives': ['zip', 'rar', '7z', 'tar', 'gz'],
        'code': ['py', 'js', 'ts', 'html', 'css', 'json', 'yaml', 'sh'],
    }
    
    results = {}
    target = Path(target_dir)
    
    for f in files:
        if not f.is_file():
            continue
        ext = f.suffix.lower().lstrip('.')
        folder = 'others'
        for cat, exts in TYPE_MAP.items():
            if ext in exts:
                folder = cat
                break
        
        dst_dir = target / folder
        dst_dir.mkdir(exist_ok=True)
        dst = dst_dir / f.name
        
        try:
            shutil.move(str(f), str(dst))
            results.setdefault(folder, []).append(f.name)
        except Exception:
            pass
    
    return results


def create_folder(name: str, target_dir: Union[str, Path]) -> Optional[Path]:
    """在目标目录创建文件夹"""
    folder = Path(target_dir) / name
    try:
        folder.mkdir(parents=True, exist_ok=True)
        return folder
    except Exception:
        return None

