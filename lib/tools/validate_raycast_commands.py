#!/usr/bin/env python3
"""
Raycast 命令验证脚本

功能：
- 检查所有 Raycast 命令文件名是否符合规范
- 验证必需元数据是否存在且非空
- 检查前缀是否在定义列表中
- 生成详细验证报告
- 支持自动修复简单问题

使用：
  python3 validate_raycast_commands.py              # 显示验证结果
  python3 validate_raycast_commands.py --fix        # 自动修复缺失的 packageName
  python3 validate_raycast_commands.py --report     # 生成详细报告到文件
"""

import argparse
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# 前缀定义和映射
PREFIX_DEFINITIONS = {
    "sec_": {"name": "秘书系统", "packageName": "秘书系统"},
    "hy_": {"name": "水利工具", "packageName": "Hydraulic"},
    "yb_": {"name": "Yabai窗口管理", "packageName": "Window Manager"},
    "docx_": {"name": "Word文档处理", "packageName": "Document Processing"},
    "xlsx_": {"name": "Excel数据处理", "packageName": "Data Processing"},
    "csv_": {"name": "CSV数据处理", "packageName": "Data Processing"},
    "md_": {"name": "Markdown处理", "packageName": "Document Processing"},
    "pptx_": {"name": "PowerPoint处理", "packageName": "Document Processing"},
    "file_": {"name": "文件操作", "packageName": "File Operations"},
    "folder_": {"name": "文件夹操作", "packageName": "File Operations"},
    "clashx_": {"name": "网络代理", "packageName": "Network"},
    "sys_": {"name": "系统工具", "packageName": "System"},
    "display_": {"name": "显示设置", "packageName": "System"},
    "app_": {"name": "应用启动", "packageName": "Apps"},
    "dingtalk_": {"name": "钉钉应用", "packageName": "Dingtalk"},
    "tts_": {"name": "文本转语音", "packageName": "TTS"},
}

# 必需元数据字段
REQUIRED_METADATA = [
    "schemaVersion",
    "title",
    "mode",
    "icon",
    "packageName",
    "description",
]

# 有效的模式
VALID_MODES = {"fullOutput", "silent", "compact"}


@dataclass
class ValidationIssue:
    """验证问题"""

    file_name: str
    issue_type: str  # 'naming', 'prefix', 'metadata', 'empty_value'
    details: str
    severity: str = "error"  # 'error', 'warning'


@dataclass
class CommandValidation:
    """单个命令的验证结果"""

    file_name: str
    file_path: Path
    is_valid: bool = True
    issues: list[ValidationIssue] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)

    def add_issue(self, issue_type: str, details: str, severity: str = "error"):
        """添加验证问题"""
        self.issues.append(ValidationIssue(self.file_name, issue_type, details, severity))
        if severity == "error":
            self.is_valid = False


class RaycastValidator:
    """Raycast 命令验证器"""

    def __init__(self, commands_dir: Path):
        self.commands_dir = commands_dir
        self.results: list[CommandValidation] = []
        self.valid_count = 0
        self.invalid_count = 0

    def validate_all(self) -> list[CommandValidation]:
        """验证所有命令"""
        if not self.commands_dir.exists():
            print(f"❌ 命令目录不存在: {self.commands_dir}")
            sys.exit(1)

        # 获取所有 .sh 文件（排除 _archived）
        sh_files = [f for f in self.commands_dir.glob("*.sh") if f.is_file() and f.parent.name != "_archived"]

        if not sh_files:
            print(f"⚠️  未找到任何 .sh 文件在 {self.commands_dir}")
            return []

        print(f"📋 开始验证 {len(sh_files)} 个命令文件...\n")

        for sh_file in sorted(sh_files):
            result = self._validate_single_file(sh_file)
            self.results.append(result)

            if result.is_valid:
                self.valid_count += 1
            else:
                self.invalid_count += 1

        return self.results

    def _validate_single_file(self, file_path: Path) -> CommandValidation:
        """验证单个文件"""
        file_name = file_path.name
        result = CommandValidation(file_name, file_path)

        # 1. 检查文件名格式
        self._validate_filename(file_name, result)

        # 2. 读取文件内容
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            result.add_issue("file_read", f"无法读取文件: {e}")
            return result

        # 3. 提取元数据
        self._extract_metadata(content, result)

        # 4. 验证元数据
        self._validate_metadata(result)

        return result

    def _validate_filename(self, file_name: str, result: CommandValidation):
        """验证文件名格式"""
        # 检查是否以 .sh 结尾
        if not file_name.endswith(".sh"):
            result.add_issue("naming", "文件名必须以 .sh 结尾")
            return

        # 检查格式 {prefix}_{function}.sh
        name_without_ext = file_name[:-3]
        if "_" not in name_without_ext:
            result.add_issue("naming", "文件名格式错误，应为 {prefix}_{function}.sh")
            return

        # 提取前缀
        parts = name_without_ext.split("_", 1)
        prefix = parts[0] + "_"

        # 检查前缀是否有效
        if prefix not in PREFIX_DEFINITIONS:
            valid_prefixes = ", ".join(PREFIX_DEFINITIONS.keys())
            result.add_issue("prefix", f"前缀 '{prefix}' 不在规范列表中。有效前缀: {valid_prefixes}")

        # 检查函数名是否为空
        if len(parts) < 2 or not parts[1]:
            result.add_issue("naming", "函数名不能为空")

    def _extract_metadata(self, content: str, result: CommandValidation):
        """从文件内容中提取元数据"""
        # 匹配 @raycast.xxx 格式
        pattern = r"#\s*@raycast\.(\w+)\s+(.+?)(?:\n|$)"
        matches = re.findall(pattern, content)

        for key, value in matches:
            result.metadata[key] = value.strip()

    def _validate_metadata(self, result: CommandValidation):
        """验证元数据"""
        # 检查必需字段
        for field_name in REQUIRED_METADATA:
            if field_name not in result.metadata:
                result.add_issue("metadata", f"缺失必需元数据: @raycast.{field_name}")
            elif not result.metadata[field_name]:
                result.add_issue("empty_value", f"元数据值为空: @raycast.{field_name}")

        # 检查 mode 是否有效
        if "mode" in result.metadata:
            mode = result.metadata["mode"]
            if mode not in VALID_MODES:
                result.add_issue("metadata", f"无效的 mode: '{mode}'，应为 {VALID_MODES}")

        # 检查 schemaVersion 是否为 1
        if "schemaVersion" in result.metadata:
            schema = result.metadata["schemaVersion"]
            if schema != "1":
                result.add_issue("metadata", f"schemaVersion 应为 '1'，当前为 '{schema}'", severity="warning")

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("📊 验证摘要")
        print("=" * 60)
        print(f"✅ 符合规范: {self.valid_count}")
        print(f"❌ 不符合规范: {self.invalid_count}")
        print(f"📈 总计: {len(self.results)}")

        if self.invalid_count == 0:
            print("\n🎉 所有命令都符合规范！")
        else:
            print(f"\n⚠️  发现 {self.invalid_count} 个命令需要修复")

    def print_detailed_report(self):
        """打印详细报告"""
        if self.invalid_count == 0:
            return

        print("\n" + "=" * 60)
        print("📋 详细问题列表")
        print("=" * 60)

        # 按问题类型分组
        issues_by_type = defaultdict(list)
        for result in self.results:
            if not result.is_valid:
                for issue in result.issues:
                    issues_by_type[issue.issue_type].append((result.file_name, issue))

        # 打印各类问题
        issue_type_names = {
            "naming": "❌ 文件名格式错误",
            "prefix": "❌ 前缀不在规范列表中",
            "metadata": "❌ 缺失或无效的元数据",
            "empty_value": "❌ 元数据值为空",
        }

        for issue_type in ["naming", "prefix", "metadata", "empty_value"]:
            if issue_type in issues_by_type:
                print(f"\n{issue_type_names[issue_type]}")
                print("-" * 60)
                for file_name, issue in issues_by_type[issue_type]:
                    print(f"  {file_name}")
                    print(f"    → {issue.details}")

    def generate_report_file(self, output_path: Path):
        """生成报告文件"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("# Raycast 命令验证报告\n\n")
            f.write(f"生成时间: {self._get_timestamp()}\n\n")

            # 摘要
            f.write("## 摘要\n\n")
            f.write(f"- 符合规范: {self.valid_count}\n")
            f.write(f"- 不符合规范: {self.invalid_count}\n")
            f.write(f"- 总计: {len(self.results)}\n\n")

            # 详细问题
            if self.invalid_count > 0:
                f.write("## 问题详情\n\n")

                issues_by_type = defaultdict(list)
                for result in self.results:
                    if not result.is_valid:
                        for issue in result.issues:
                            issues_by_type[issue.issue_type].append((result.file_name, issue))

                issue_type_names = {
                    "naming": "文件名格式错误",
                    "prefix": "前缀不在规范列表中",
                    "metadata": "缺失或无效的元数据",
                    "empty_value": "元数据值为空",
                }

                for issue_type in ["naming", "prefix", "metadata", "empty_value"]:
                    if issue_type in issues_by_type:
                        f.write(f"### {issue_type_names[issue_type]}\n\n")
                        for file_name, issue in issues_by_type[issue_type]:
                            f.write(f"- **{file_name}**: {issue.details}\n")
                        f.write("\n")

            # 符合规范的命令
            if self.valid_count > 0:
                f.write("## 符合规范的命令\n\n")
                for result in self.results:
                    if result.is_valid:
                        f.write(f"- {result.file_name}\n")

        print(f"\n✅ 报告已生成: {output_path}")

    @staticmethod
    def _get_timestamp() -> str:
        """获取当前时间戳"""
        from datetime import datetime

        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def auto_fix(self) -> int:
        """自动修复缺失的 packageName"""
        fixed_count = 0

        for result in self.results:
            if "packageName" not in result.metadata:
                # 从文件名提取前缀
                file_name = result.file_name[:-3]  # 去掉 .sh
                prefix = file_name.split("_")[0] + "_"

                if prefix in PREFIX_DEFINITIONS:
                    package_name = PREFIX_DEFINITIONS[prefix]["packageName"]
                    self._add_package_name(result.file_path, package_name)
                    fixed_count += 1
                    print(f"✅ 已修复 {result.file_name}: 添加 packageName = {package_name}")

        return fixed_count

    def _add_package_name(self, file_path: Path, package_name: str):
        """向文件添加 packageName 元数据"""
        with open(file_path, encoding="utf-8") as f:
            lines = f.readlines()

        # 找到最后一个 @raycast 行
        last_raycast_idx = -1
        for i, line in enumerate(lines):
            if "@raycast." in line:
                last_raycast_idx = i

        if last_raycast_idx >= 0:
            # 在最后一个 @raycast 行后插入
            insert_idx = last_raycast_idx + 1
            new_line = f"# @raycast.packageName {package_name}\n"
            lines.insert(insert_idx, new_line)

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Raycast 命令验证脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 validate_raycast_commands.py              # 显示验证结果
  python3 validate_raycast_commands.py --fix        # 自动修复缺失的 packageName
  python3 validate_raycast_commands.py --report     # 生成详细报告到文件
        """,
    )

    parser.add_argument("--fix", action="store_true", help="自动修复缺失的 packageName")
    parser.add_argument("--report", action="store_true", help="生成详细报告到文件")
    parser.add_argument(
        "--dir",
        type=Path,
        default=Path.home() / "useful_scripts" / "raycast" / "commands",
        help="Raycast 命令目录（默认: ~/useful_scripts/raycast/commands）",
    )

    args = parser.parse_args()

    # 创建验证器
    validator = RaycastValidator(args.dir)

    # 执行验证
    validator.validate_all()

    # 打印摘要
    validator.print_summary()

    # 打印详细报告
    validator.print_detailed_report()

    # 自动修复
    if args.fix:
        print("\n" + "=" * 60)
        print("🔧 自动修复模式")
        print("=" * 60)
        fixed_count = validator.auto_fix()
        print(f"\n✅ 已修复 {fixed_count} 个文件")

    # 生成报告文件
    if args.report:
        report_path = Path.home() / "useful_scripts" / "raycast_validation_report.md"
        validator.generate_report_file(report_path)

    # 返回退出码
    sys.exit(0 if validator.invalid_count == 0 else 1)


if __name__ == "__main__":
    main()
