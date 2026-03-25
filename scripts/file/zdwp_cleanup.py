#!/usr/bin/env python3
"""
ZDWP 文件清理工具

功能：
  规则 1：删除垃圾文件（.DS_Store, Thumbs.db, 临时文件, __pycache__ 等）
  规则 2：疑似重复文件移到 _trash/（副本、copy、编号重复）
  规则 3：命名规范化（日期标准化、版本标准化、不明文件名识别）

用法：
  zdwp_cleanup.py                     # dry-run，生成报告
  zdwp_cleanup.py --execute            # 执行清理
  zdwp_cleanup.py --rules 1,2          # 只运行规则 1 和 2
  zdwp_cleanup.py --target ~/Work/zdwp # 指定目标目录
"""

import argparse
import json
import os
import re
import shutil
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

DEFAULT_TARGET = Path.home() / "Work" / "zdwp"

JUNK_FILES = {".DS_Store", "Thumbs.db"}
JUNK_EXTENSIONS = {".pyc", ".tmp", ".bak"}
JUNK_DIRS = {"__pycache__", "node_modules", ".next"}
SKIP_DIRS = {".git", "_trash"}
# 虚拟环境和依赖目录，规则 2/3 不应扫描其内部文件
VENV_DIRS = {"venv", ".venv", "env", ".env", "site-packages", "archived"}

BINARY_EXTENSIONS = {".docx", ".pdf", ".xlsx", ".xls", ".pptx", ".doc", ".dwg"}

# 文件名末尾的重复编号模式：文件名 (1).ext, 文件名（2）.ext
# 只匹配扩展名前的编号，且编号数字较小（1-9），避免误匹配正式编号如 (2024)
RE_NUMBER_SUFFIX = re.compile(r"[\s]?[\(（]([1-9])[\)）]$")
# 文件名中的 4 位日期模式，如 0903、0123、1226
RE_DATE_4DIGIT = re.compile(r"(?<!\d)(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)")
# Word 临时锁文件 ~$*.docx / ~$*.doc
RE_WORD_LOCK = re.compile(r"^~\$.*\.docx?$", re.IGNORECASE)
# 副本/copy 关键词——要求 copy 前后有分隔符或在首尾位置，避免匹配 test_copy.py
RE_COPY_KEYWORD = re.compile(r"副本|(?:^|[\s_\-])copy(?:[\s_\-]|$)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def human_size(nbytes: int) -> str:
    """将字节数转为人类可读的大小字符串。"""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(nbytes) < 1024:
            return f"{nbytes:.1f} {unit}" if unit != "B" else f"{nbytes} {unit}"
        nbytes /= 1024
    return f"{nbytes:.1f} TB"


def should_skip_dir(name: str) -> bool:
    """判断是否应跳过此目录。"""
    return name in SKIP_DIRS


def iter_all_paths(root: Path):
    """递归遍历 root 下所有路径，跳过 .git 和 _trash 目录。
    yield (path, is_dir)
    """
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            if should_skip_dir(entry.name):
                continue
            yield entry, True
            yield from iter_all_paths(entry)
        else:
            yield entry, False


def get_dir_size(p: Path) -> tuple[int, int]:
    """返回目录的 (文件数, 总字节数)。"""
    count = 0
    total = 0
    for root, _dirs, files in os.walk(p):
        for f in files:
            fp = Path(root) / f
            try:
                total += fp.stat().st_size
                count += 1
            except OSError:
                pass
    return count, total


def read_docx_first_paragraphs(filepath: Path, n: int = 3) -> str | None:
    """尝试读取 docx 的前 n 段文字。失败返回 None。"""
    try:
        import docx

        doc = docx.Document(str(filepath))
        texts = []
        for i, para in enumerate(doc.paragraphs):
            if i >= n:
                break
            t = para.text.strip()
            if t:
                texts.append(t)
        return "\n".join(texts) if texts else None
    except Exception:
        return None


def infer_year_for_4digit_date(mmdd: str, file_mtime: float) -> int:
    """根据 mtime 推断 4 位日期中的年份。
    策略：取 mtime 所在年份；如果 mmdd 对应的日期比 mtime 晚超过 6 个月，
    则认为是前一年。
    """
    mtime_dt = datetime.fromtimestamp(file_mtime)
    year = mtime_dt.year
    month = int(mmdd[:2])
    day = int(mmdd[2:])
    try:
        candidate = datetime(year, month, day)
    except ValueError:
        return year
    # 如果候选日期比 mtime 晚超过 180 天，可能是去年的
    if (candidate - mtime_dt).days > 180:
        return year - 1
    return year


def strip_number_suffix(name: str) -> str:
    """去掉文件名中的编号后缀，如 '文件(1)' -> '文件'。
    同时处理编号前可能有的空格/横杠。
    """
    result = RE_NUMBER_SUFFIX.sub("", name)
    # 清理编号前残留的空格、横杠、下划线
    result = re.sub(r"[\s_-]+$", "", result)
    return result


def is_short_or_opaque_name(stem: str) -> bool:
    """判断文件名是否"不明"——太短或只有英文+数字。"""
    if len(stem) < 5:
        return True
    # 只有 ASCII 字母、数字、下划线、横杠
    if re.fullmatch(r"[a-zA-Z0-9_\-]+", stem):
        return True
    return False


# ---------------------------------------------------------------------------
# 规则 1：垃圾文件
# ---------------------------------------------------------------------------


class Rule1:
    """无条件删除垃圾文件。"""

    def __init__(self):
        # {类型描述: [(path, size_bytes)]}
        self.items: dict[str, list[tuple[Path, int]]] = defaultdict(list)
        # 目录类型: {类型描述: [(dir_path, file_count, size_bytes)]}
        self.dir_items: dict[str, list[tuple[Path, int, int]]] = defaultdict(list)

    def scan(self, root: Path):
        """扫描垃圾文件。"""
        for entry in sorted(root.iterdir()):
            if entry.is_dir():
                if should_skip_dir(entry.name):
                    continue
                if entry.name in JUNK_DIRS:
                    fc, sz = get_dir_size(entry)
                    self.dir_items[entry.name].append((entry, fc, sz))
                    continue
                self.scan(entry)
            else:
                self._check_file(entry)

    def _check_file(self, p: Path):
        name = p.name
        try:
            size = p.stat().st_size
        except OSError:
            size = 0

        if name in JUNK_FILES:
            self.items[name].append((p, size))
        elif p.suffix.lower() in JUNK_EXTENSIONS:
            self.items[p.suffix.lower()].append((p, size))
        elif RE_WORD_LOCK.match(name):
            self.items["~$*.docx（锁文件）"].append((p, size))

    @property
    def total_files(self) -> int:
        count = sum(len(v) for v in self.items.values())
        count += sum(fc for entries in self.dir_items.values() for _, fc, _ in entries)
        return count

    @property
    def total_dirs(self) -> int:
        return sum(len(v) for v in self.dir_items.values())

    @property
    def total_bytes(self) -> int:
        total = sum(sz for entries in self.items.values() for _, sz in entries)
        total += sum(sz for entries in self.dir_items.values() for _, _, sz in entries)
        return total

    def report_md(self, root: Path) -> str:
        lines = [
            "## 规则 1：垃圾文件（直接删除）",
            f"共 {self.total_files + self.total_dirs} 项"
            f"（{self.total_files} 个文件, {self.total_dirs} 个目录），"
            f"释放 {human_size(self.total_bytes)}",
            "",
            "| 类型 | 数量 | 体积 |",
            "|------|------|------|",
        ]
        for typ, entries in sorted(self.items.items()):
            sz = sum(s for _, s in entries)
            lines.append(f"| {typ} | {len(entries)} | {human_size(sz)} |")
        for typ, entries in sorted(self.dir_items.items()):
            dir_count = len(entries)
            file_count = sum(fc for _, fc, _ in entries)
            sz = sum(s for _, _, s in entries)
            lines.append(f"| {typ}/ | {dir_count} dirs, {file_count} files | {human_size(sz)} |")
        return "\n".join(lines)

    def execute(self, root: Path):
        """执行删除。"""
        count = 0
        for entries in self.items.values():
            for p, _ in entries:
                try:
                    p.unlink()
                    count += 1
                    print(f"  删除: {p.relative_to(root)}")
                except OSError as e:
                    print(f"  失败: {p.relative_to(root)} — {e}", file=sys.stderr)
        for entries in self.dir_items.values():
            for p, fc, _ in entries:
                try:
                    shutil.rmtree(p)
                    count += fc
                    print(f"  删除目录: {p.relative_to(root)}")
                except OSError as e:
                    print(f"  失败: {p.relative_to(root)} — {e}", file=sys.stderr)
        print(f"规则 1 完成：删除了 {count} 项")


# ---------------------------------------------------------------------------
# 规则 2：疑似重复
# ---------------------------------------------------------------------------


class Rule2:
    """疑似重复文件处理。"""

    def __init__(self):
        # 有原件的重复：[(dup_path, original_path)]
        self.duplicates: list[tuple[Path, Path]] = []
        # 副本/copy 关键词：[(path, original_or_none)]
        self.copy_keyword: list[tuple[Path, Path | None]] = []
        # 孤立重复（编号文件但无原件）
        self.orphans: list[Path] = []

    def scan(self, root: Path):
        # 按目录分组扫描
        for dirpath, dirnames, filenames in os.walk(root):
            dp = Path(dirpath)
            # 跳过特殊目录（含 .git、_trash、垃圾目录、虚拟环境）
            dirnames[:] = [d for d in dirnames if not should_skip_dir(d) and d not in JUNK_DIRS and d not in VENV_DIRS]

            # 建立目录内文件名索引（小写 stem -> 完整 Path）
            name_index: dict[str, list[Path]] = defaultdict(list)
            for fn in filenames:
                fp = dp / fn
                name_index[fp.stem.lower()].append(fp)

            for fn in filenames:
                fp = dp / fn
                stem = fp.stem
                ext = fp.suffix

                # 检查副本/copy 关键词
                if RE_COPY_KEYWORD.search(stem):
                    # 尝试找原件：去掉"副本"/"copy"及前后的分隔符
                    cleaned = RE_COPY_KEYWORD.sub("", stem).strip()
                    cleaned = re.sub(r"[\s_\-]+$", "", cleaned)
                    cleaned = re.sub(r"^[\s_\-]+", "", cleaned)
                    if cleaned:
                        original = dp / (cleaned + ext)
                        if original.exists() and original != fp:
                            self.duplicates.append((fp, original))
                        else:
                            self.copy_keyword.append((fp, None))
                    else:
                        self.copy_keyword.append((fp, None))
                    continue

                # 检查编号后缀
                match = RE_NUMBER_SUFFIX.search(stem)
                if match:
                    base_stem = strip_number_suffix(stem)
                    if base_stem:
                        original = dp / (base_stem + ext)
                        if original.exists() and original != fp:
                            self.duplicates.append((fp, original))
                        else:
                            # 检查是否有去掉编号后的文件
                            found = False
                            for candidate in name_index.get(base_stem.lower(), []):
                                if candidate != fp and candidate.suffix.lower() == ext.lower():
                                    self.duplicates.append((fp, candidate))
                                    found = True
                                    break
                            if not found:
                                self.orphans.append(fp)

    def report_md(self, root: Path) -> str:
        lines = [
            "## 规则 2：疑似重复（移到 _trash/）",
            f"共 {len(self.duplicates) + len(self.copy_keyword)} 个文件",
            "",
        ]

        if self.duplicates or self.copy_keyword:
            lines.extend(
                [
                    "| 文件 | 原件 | 操作 |",
                    "|------|------|------|",
                ]
            )
            for dup, orig in self.duplicates:
                lines.append(f"| {dup.relative_to(root)} | {orig.relative_to(root)} | → _trash/ |")
            for dup, orig in self.copy_keyword:
                orig_str = str(orig.relative_to(root)) if orig else "（关键词匹配）"
                lines.append(f"| {dup.relative_to(root)} | {orig_str} | → _trash/ |")
        else:
            lines.append("无疑似重复文件。")

        if self.orphans:
            lines.extend(
                [
                    "",
                    "### 孤立重复（无原件，保留）",
                    "",
                    "| 文件 | 备注 |",
                    "|------|------|",
                ]
            )
            for p in self.orphans:
                lines.append(f"| {p.relative_to(root)} | 同目录无原件，保留 |")

        return "\n".join(lines)

    def execute(self, root: Path):
        """将重复文件移到 _trash/。"""
        trash = root / "_trash"
        count = 0
        all_dups = [(p, orig) for p, orig in self.duplicates]
        all_dups += [(p, orig) for p, orig in self.copy_keyword]

        for dup, _ in all_dups:
            rel = dup.relative_to(root)
            dest = trash / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(dup), str(dest))
                count += 1
                print(f"  移动: {rel} → _trash/{rel}")
            except OSError as e:
                print(f"  失败: {rel} — {e}", file=sys.stderr)
        print(f"规则 2 完成：移动了 {count} 个文件到 _trash/")


# ---------------------------------------------------------------------------
# 规则 3：命名规范化
# ---------------------------------------------------------------------------


class Rule3:
    """命名规范化，生成重命名建议。"""

    def __init__(self):
        # [(original_path, suggested_name, reason)]
        self.suggestions: list[tuple[Path, str, str]] = []

    def scan(self, root: Path):
        # 收集所有二进制文件，按目录和基础名分组
        # dir -> base_name -> [(path, date_str_or_none, mtime)]
        dir_groups: dict[Path, dict[str, list[tuple[Path, str | None, float]]]] = defaultdict(lambda: defaultdict(list))

        binary_files: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dp = Path(dirpath)
            dirnames[:] = [
                d
                for d in dirnames
                if not should_skip_dir(d) and d not in JUNK_DIRS and d not in VENV_DIRS and d != "_trash"
            ]
            for fn in filenames:
                fp = dp / fn
                if fp.suffix.lower() in BINARY_EXTENSIONS:
                    binary_files.append(fp)

        total = len(binary_files)
        print(f"规则 3：扫描 {total} 个二进制文件...")

        for i, fp in enumerate(binary_files, 1):
            if i % 50 == 0 or i == total:
                print(f"  进度: {i}/{total}")

            stem = fp.stem
            ext = fp.suffix
            parent = fp.parent

            try:
                mtime = fp.stat().st_mtime
            except OSError:
                mtime = 0

            # 提取 4 位日期
            date_match = RE_DATE_4DIGIT.search(stem)
            date_str = date_match.group(0) if date_match else None

            # 确定基础名（去掉日期部分）
            if date_str:
                base_name = stem.replace(date_str, "").strip("_- ")
            else:
                base_name = stem

            # 去掉已有的 YYYYMMDD 前缀
            yyyymmdd_match = re.match(r"^(\d{8})[_\-\s]*(.*)", base_name)
            if yyyymmdd_match:
                # 已经有标准日期前缀，跳过日期标准化
                continue

            dir_groups[parent][base_name].append((fp, date_str, mtime))

        # 处理版本标准化（同一基础名多个日期版本）
        processed_paths: set[Path] = set()
        for _, groups in dir_groups.items():
            for _, file_list in groups.items():
                dated = [(fp, ds, mt) for fp, ds, mt in file_list if ds is not None]
                if len(dated) >= 2:
                    # 多版本：按日期排序，标准化为 v1, v2...
                    dated_with_full = []
                    for fp, ds, mt in dated:
                        year = infer_year_for_4digit_date(ds, mt)
                        full_date = f"{year}{ds}"
                        dated_with_full.append((fp, full_date, mt))
                    dated_with_full.sort(key=lambda x: x[1])

                    clean_base = base_name if base_name else "文件"
                    for idx, (fp, full_date, _) in enumerate(dated_with_full, 1):
                        new_name = f"{clean_base}_v{idx}_{full_date}{fp.suffix}"
                        if new_name != fp.name:
                            self.suggestions.append((fp, new_name, "版本标准化"))
                        processed_paths.add(fp)

        # 处理单文件日期标准化和不明文件名识别
        for _, groups in dir_groups.items():
            for _, file_list in groups.items():
                for fp, date_str, mtime in file_list:
                    if fp in processed_paths:
                        continue

                    stem = fp.stem
                    ext = fp.suffix

                    # 3a: 日期标准化
                    if date_str:
                        year = infer_year_for_4digit_date(date_str, mtime)
                        full_date = f"{year}{date_str}"
                        # 去掉原日期，加标准前缀
                        clean_name = stem.replace(date_str, "").strip("_- ")
                        if clean_name:
                            new_name = f"{full_date}_{clean_name}{ext}"
                        else:
                            new_name = f"{full_date}{ext}"
                        if new_name != fp.name:
                            self.suggestions.append((fp, new_name, "日期标准化"))
                        processed_paths.add(fp)
                    else:
                        # 无日期，用 mtime 添加前缀
                        mtime_date = datetime.fromtimestamp(mtime).strftime("%Y%m%d")
                        new_name = f"{mtime_date}_{stem}{ext}"
                        if new_name != fp.name:
                            self.suggestions.append((fp, new_name, "添加日期前缀（mtime）"))
                        processed_paths.add(fp)

                    # 3c: 不明文件名识别
                    if is_short_or_opaque_name(stem) and ext.lower() == ".docx":
                        content = read_docx_first_paragraphs(fp)
                        if content:
                            # 取前 30 字符作为建议名
                            preview = content.split("\n")[0][:30].strip()
                            # 清理不能用于文件名的字符
                            safe_preview = re.sub(r'[\\/:*?"<>|\n\r]', "", preview)
                            if safe_preview:
                                content_name = f"{safe_preview}_{stem}{ext}"
                                # 找到对应的建议并更新
                                updated = False
                                for j, (sp, sn, _sr) in enumerate(self.suggestions):
                                    if sp == fp:
                                        # 在已有建议基础上，用内容识别的名字替换
                                        date_prefix = sn.split("_")[0] if "_" in sn else ""
                                        if date_prefix and date_prefix.isdigit() and len(date_prefix) == 8:
                                            content_name = f"{date_prefix}_{safe_preview}{ext}"
                                        self.suggestions[j] = (
                                            fp,
                                            content_name,
                                            f'内容识别(首段:"{preview[:20]}...")',
                                        )
                                        updated = True
                                        break
                                if not updated:
                                    self.suggestions.append(
                                        (
                                            fp,
                                            content_name,
                                            f'内容识别(首段:"{preview[:20]}...")',
                                        )
                                    )

    def report_md(self, root: Path) -> str:
        lines = [
            "## 规则 3：重命名建议",
            f"共 {len(self.suggestions)} 个文件",
            "",
        ]
        if self.suggestions:
            lines.extend(
                [
                    "| 原文件名 | 建议新名 | 原因 |",
                    "|----------|----------|------|",
                ]
            )
            for fp, new_name, reason in self.suggestions:
                rel = fp.relative_to(root)
                lines.append(f"| {rel} | {new_name} | {reason} |")
        else:
            lines.append("无需重命名。")
        return "\n".join(lines)

    def export_json(self, root: Path, output: Path):
        """导出重命名计划为 JSON，供用户确认后执行。"""
        data = []
        for fp, new_name, reason in self.suggestions:
            data.append(
                {
                    "original": str(fp),
                    "relative": str(fp.relative_to(root)),
                    "suggested_name": new_name,
                    "reason": reason,
                    "confirmed": False,
                }
            )
        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"重命名计划已导出到: {output}")

    def execute(self, root: Path):
        """从 _cleanup_confirmed.json 读取已确认的重命名并执行。"""
        confirmed_path = root / "_cleanup_confirmed.json"
        if not confirmed_path.exists():
            print("规则 3：未找到 _cleanup_confirmed.json，跳过重命名。")
            print(f"  请先运行 dry-run 生成报告，编辑 {confirmed_path} 中的 confirmed 字段后再执行。")
            return

        with open(confirmed_path, encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for item in data:
            if not item.get("confirmed", False):
                continue
            original = Path(item["original"])
            new_name = item["suggested_name"]
            if not original.exists():
                print(f"  跳过（文件不存在）: {original}")
                continue
            dest = original.parent / new_name
            if dest.exists():
                print(f"  跳过（目标已存在）: {dest}")
                continue
            try:
                original.rename(dest)
                count += 1
                print(f"  重命名: {original.name} → {new_name}")
            except OSError as e:
                print(f"  失败: {original.name} — {e}", file=sys.stderr)
        print(f"规则 3 完成：重命名了 {count} 个文件")


# ---------------------------------------------------------------------------
# 主函数
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="ZDWP 文件清理工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="只生成报告，不执行操作（默认）",
    )
    mode_group.add_argument(
        "--execute",
        action="store_true",
        help="执行清理操作",
    )
    parser.add_argument(
        "--rules",
        type=str,
        default="1,2,3",
        help="选择运行哪些规则，逗号分隔（默认: 1,2,3）",
    )
    parser.add_argument(
        "--target",
        type=Path,
        default=DEFAULT_TARGET,
        help=f"目标目录（默认: {DEFAULT_TARGET}）",
    )
    args = parser.parse_args()

    # --execute 会让 --dry-run 为 True（因为 default），需要手动处理
    is_execute = args.execute
    root = args.target.expanduser().resolve()
    rules = set(int(r.strip()) for r in args.rules.split(","))

    if not root.exists():
        print(f"错误：目标目录不存在: {root}", file=sys.stderr)
        sys.exit(1)

    mode_str = "execute" if is_execute else "dry-run"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"ZDWP 文件清理工具 | 目标: {root} | 模式: {mode_str} | 规则: {args.rules}")
    print(f"时间: {now}")
    print("=" * 60)

    report_parts = [
        "# ZDWP 文件清理报告",
        f"> 生成时间: {now} | 模式: {mode_str} | 规则: {args.rules}",
        "",
    ]

    # 规则 1
    if 1 in rules:
        print("\n[规则 1] 扫描垃圾文件...")
        r1 = Rule1()
        r1.scan(root)
        print(f"  发现 {r1.total_files} 个文件, {r1.total_dirs} 个目录，共 {human_size(r1.total_bytes)}")
        report_parts.append(r1.report_md(root))
        report_parts.append("")
        if is_execute:
            r1.execute(root)

    # 规则 2
    if 2 in rules:
        print("\n[规则 2] 扫描疑似重复...")
        r2 = Rule2()
        r2.scan(root)
        total_dups = len(r2.duplicates) + len(r2.copy_keyword)
        print(f"  发现 {total_dups} 个重复文件，{len(r2.orphans)} 个孤立重复")
        report_parts.append(r2.report_md(root))
        report_parts.append("")
        if is_execute:
            r2.execute(root)

    # 规则 3
    if 3 in rules:
        print("\n[规则 3] 分析文件命名...")
        r3 = Rule3()
        r3.scan(root)
        print(f"  生成 {len(r3.suggestions)} 条重命名建议")
        report_parts.append(r3.report_md(root))
        report_parts.append("")

        if not is_execute:
            # dry-run 模式：导出 JSON 供确认
            if r3.suggestions:
                json_path = root / "_cleanup_rename_plan.json"
                r3.export_json(root, json_path)
        else:
            r3.execute(root)

    # 写报告
    if not is_execute:
        report_path = root / "_cleanup_report.md"
        report_content = "\n".join(report_parts)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        print(f"\n{'=' * 60}")
        print(f"报告已生成: {report_path}")
        if 3 in rules:
            print(f"重命名计划: {root / '_cleanup_rename_plan.json'}")
            print("\n下一步：")
            print(f"  1. 查看报告: cat {report_path}")
            print("  2. 编辑重命名计划，将需要执行的项 confirmed 改为 true")
            print(f"     cp {root / '_cleanup_rename_plan.json'} {root / '_cleanup_confirmed.json'}")
            print(f"  3. 执行: python3 {__file__} --execute")


if __name__ == "__main__":
    main()
