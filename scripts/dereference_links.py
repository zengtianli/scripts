#!/usr/bin/env python3
"""
dereference_links.py - 将符号链接替换为实际文件

用法:
    python3 dereference_links.py /path/to/project
    python3 dereference_links.py . --dry-run  # 预览模式

功能:
    递归扫描目录，将所有符号链接替换为实际文件/目录
    用于分享项目前，确保接收方能看到完整内容
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List

def find_symlinks(target_dir: Path) -> List[Path]:
    """递归查找所有符号链接"""
    links = []

    try:
        for root, dirs, files in os.walk(target_dir, followlinks=False):
            root_path = Path(root)

            # 检查目录是否是符号链接
            # 注意：需要在遍历前检查，避免进入符号链接目录
            for d in list(dirs):  # 使用 list() 创建副本，因为可能修改 dirs
                dir_path = root_path / d
                if dir_path.is_symlink():
                    links.append(dir_path)
                    dirs.remove(d)  # 不进入符号链接目录

            # 检查文件是否是符号链接
            for f in files:
                file_path = root_path / f
                if file_path.is_symlink():
                    links.append(file_path)

    except PermissionError as e:
        print(f"⚠️  权限错误: {e}")

    return links

def dereference_links(target_dir: Path, dry_run: bool = False) -> None:
    """将符号链接替换为实际文件"""

    print(f"🔍 扫描目录: {target_dir.absolute()}")

    # 查找所有符号链接
    links = find_symlinks(target_dir)

    if not links:
        print("✅ 没有找到符号链接")
        return

    print(f"📊 找到 {len(links)} 个符号链接\n")

    success_count = 0
    error_count = 0

    for link in links:
        try:
            # 获取真实路径
            real_path = link.resolve(strict=True)

            # 计算相对路径（便于显示）
            try:
                rel_link = link.relative_to(target_dir)
            except ValueError:
                rel_link = link

            print(f"📋 {rel_link}")
            print(f"   → {real_path}")

            if dry_run:
                print(f"   [DRY RUN] 将会替换")
                success_count += 1
                continue

            # 删除符号链接
            link.unlink()

            # 复制真实文件/目录
            if real_path.is_dir():
                shutil.copytree(real_path, link, symlinks=False)
                print(f"   ✅ 已复制目录")
            else:
                shutil.copy2(real_path, link)
                print(f"   ✅ 已复制文件")

            success_count += 1

        except FileNotFoundError:
            print(f"   ❌ 目标不存在: {link}")
            error_count += 1
        except PermissionError as e:
            print(f"   ❌ 权限错误: {e}")
            error_count += 1
        except Exception as e:
            print(f"   ❌ 错误: {e}")
            error_count += 1

        print()  # 空行分隔

    # 总结
    print("=" * 60)
    if dry_run:
        print(f"🎉 预览完成！找到 {success_count} 个符号链接")
        print(f"   运行时将替换这些链接为实际文件")
    else:
        print(f"🎉 完成！")
        print(f"   ✅ 成功: {success_count}")
        if error_count > 0:
            print(f"   ❌ 失败: {error_count}")

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python3 dereference_links.py <目录> [--dry-run]")
        print()
        print("示例:")
        print("  python3 dereference_links.py .                # 当前目录")
        print("  python3 dereference_links.py ~/project        # 指定目录")
        print("  python3 dereference_links.py . --dry-run      # 预览模式")
        sys.exit(1)

    target = Path(sys.argv[1]).expanduser().resolve()
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv

    if not target.exists():
        print(f"❌ 目录不存在: {target}")
        sys.exit(1)

    if not target.is_dir():
        print(f"❌ 不是目录: {target}")
        sys.exit(1)

    if dry_run:
        print("🔍 预览模式（不会实际修改文件）\n")

    dereference_links(target, dry_run)

if __name__ == "__main__":
    main()
