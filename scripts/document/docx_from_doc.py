#!/usr/bin/env python3
"""
将 .doc 文件转换为 .docx 格式（使用 macOS textutil）
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_error, show_info, show_success
from finder import get_input_files


def convert_doc_to_docx(doc_path: str) -> bool:
    """将单个 .doc 文件转换为 .docx"""
    input_path = Path(doc_path)
    output_path = input_path.with_suffix(".docx")

    try:
        subprocess.run(
            ["textutil", "-convert", "docx", str(input_path), "-output", str(output_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        show_success(f"{input_path.name} -> {output_path.name}")
        return True
    except subprocess.CalledProcessError as e:
        show_error(f"{input_path.name}: {e.stderr.strip()}")
        return False


if __name__ == "__main__":
    files = get_input_files(sys.argv[1:], expected_ext="doc")
    if not files:
        sys.exit(1)

    success = sum(1 for f in files if convert_doc_to_docx(f))
    show_info(f"完成：{success}/{len(files)} 个文件转换成功")
