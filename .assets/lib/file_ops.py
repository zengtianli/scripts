#!/usr/bin/env python3
"""
文件操作工具模块
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Optional, Union

from display import show_error, show_warning, show_info


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


def check_command_exists(command: str) -> bool:
    """检查命令是否存在"""
    return shutil.which(command) is not None


def fatal_error(message: str):
    """致命错误 - 立即退出"""
    show_error(message)
    sys.exit(1)


def get_file_basename(filepath: str) -> str:
    """获取文件名（不含扩展名）"""
    return Path(filepath).stem


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


# ===== 文件批量操作 =====

def add_prefix(files: List[Path], prefix: str) -> List[tuple]:
    """批量添加文件名前缀"""
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
