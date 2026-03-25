#!/usr/bin/env python3
"""
文件系统变化追踪器
监控关键目录，追踪今天新建、修改的文件
"""

import json
import os
import sys
from datetime import date, datetime
from pathlib import Path


class FileTracker:
    """文件系统变化追踪器"""

    # 监控的关键目录
    WATCH_DIRS = {
        "work": os.path.expanduser("~/work"),
        "personal": os.path.expanduser("~/cursor-shared"),
        "zdwp": os.path.expanduser("~/Downloads/zdwp"),
    }

    # 忽略的目录和文件
    IGNORE_PATTERNS = {
        ".git",
        ".next",
        "__pycache__",
        ".DS_Store",
        "node_modules",
        ".pnpm",
        ".cache",
        ".venv",
        "dist",
        "build",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".turbo",
    }

    def __init__(self, target_date: date = None):
        """
        初始化追踪器

        Args:
            target_date: 目标日期，默认为今天
        """
        self.target_date = target_date or date.today()
        self.work_files: list[dict] = []
        self.personal_files: list[dict] = []

    def should_ignore(self, path: str) -> bool:
        """检查路径是否应该被忽略"""
        parts = Path(path).parts
        return any(part in self.IGNORE_PATTERNS for part in parts)

    def get_file_action(self, mtime: float) -> str:
        """
        根据修改时间判断文件操作类型

        Args:
            mtime: 文件修改时间戳

        Returns:
            'created' 或 'modified'
        """
        # 简化判断：假设 ctime 和 mtime 接近则为新建
        # 实际应用中可以通过 git status 或其他方式更准确判断
        return "modified"

    def format_timestamp(self, mtime: float) -> str:
        """将时间戳格式化为 ISO 8601 格式"""
        return datetime.fromtimestamp(mtime).isoformat()

    def track_directory(self, dir_path: str, category: str) -> None:
        """
        追踪单个目录

        Args:
            dir_path: 目录路径
            category: 分类 ('work' 或 'personal')
        """
        if not os.path.exists(dir_path):
            return

        for root, dirs, files in os.walk(dir_path):
            # 原地修改 dirs 列表以跳过忽略的目录
            dirs[:] = [d for d in dirs if not self.should_ignore(os.path.join(root, d))]

            for filename in files:
                if self.should_ignore(filename):
                    continue

                filepath = os.path.join(root, filename)

                try:
                    stat_info = os.stat(filepath)
                    mtime = stat_info.st_mtime
                    file_date = datetime.fromtimestamp(mtime).date()

                    # 只追踪目标日期的文件
                    if file_date == self.target_date:
                        file_record = {
                            "path": filepath,
                            "action": self.get_file_action(mtime),
                            "time": self.format_timestamp(mtime),
                            "size": stat_info.st_size,
                        }

                        if category == "work":
                            self.work_files.append(file_record)
                        elif category == "personal":
                            self.personal_files.append(file_record)

                except (OSError, ValueError):
                    # 跳过无法访问的文件
                    continue

    def track_all(self) -> None:
        """追踪所有监控目录"""
        for category, dir_path in self.WATCH_DIRS.items():
            if category == "work":
                self.track_directory(dir_path, "work")
            elif category in ("personal", "zdwp"):
                # zdwp 属于 personal 分类
                self.track_directory(dir_path, "personal")

    def sort_files(self) -> None:
        """按时间排序文件列表"""
        self.work_files.sort(key=lambda x: x["time"])
        self.personal_files.sort(key=lambda x: x["time"])

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "date": self.target_date.isoformat(),
            "work_files": self.work_files,
            "personal_files": self.personal_files,
            "summary": {
                "work_count": len(self.work_files),
                "personal_count": len(self.personal_files),
                "total_count": len(self.work_files) + len(self.personal_files),
            },
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="文件系统变化追踪器")
    parser.add_argument(
        "--date",
        type=str,
        help="目标日期 (YYYY-MM-DD 格式，默认为今天)",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="输出文件路径 (默认输出到 stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="美化输出",
    )

    args = parser.parse_args()

    # 解析目标日期
    target_date = None
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            print("错误：日期格式不正确，应为 YYYY-MM-DD", file=sys.stderr)
            sys.exit(1)

    # 创建追踪器并执行追踪
    tracker = FileTracker(target_date)
    tracker.track_all()
    tracker.sort_files()

    # 生成输出
    output = tracker.to_json(indent=2 if args.pretty else None)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
