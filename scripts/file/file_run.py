#!/usr/bin/env python3

import os
import shutil
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from display import show_error, show_info, show_success
from finder import get_input_files

PYTHON_PATH = shutil.which("python3") or "python3"


def run_script(file_path):
    """运行单个脚本"""
    file_ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    script_dir = os.path.dirname(file_path)

    if file_ext not in [".sh", ".py"]:
        return filename, False, "不是 shell 脚本或 python 文件"

    if file_ext == ".sh":
        st = os.stat(file_path)
        if not (st.st_mode & stat.S_IXUSR):
            os.chmod(file_path, st.st_mode | stat.S_IXUSR)

    try:
        if file_ext == ".py":
            result = subprocess.run(
                [PYTHON_PATH, file_path], capture_output=True, text=True, cwd=script_dir, timeout=300
            )
        else:
            result = subprocess.run(
                [file_path], capture_output=True, text=True, cwd=script_dir, shell=True, timeout=300
            )
        output = result.stdout + result.stderr
        return filename, result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return filename, False, "运行超时（5分钟）"
    except Exception as e:
        return filename, False, str(e)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"

    if mode == "parallel":
        files = get_input_files([], allow_multiple=True)
        if not files:
            return

        valid_files = [f for f in files if os.path.splitext(f)[1].lower() in [".sh", ".py"]]
        if not valid_files:
            show_error("没有选中的 shell 脚本或 python 文件")
            return

        show_info(f"开始并行运行 {len(valid_files)}/{len(files)} 个文件...")

        results = []
        with ThreadPoolExecutor(max_workers=min(len(valid_files), 4)) as executor:
            futures = {executor.submit(run_script, f): f for f in valid_files}
            for future in as_completed(futures):
                results.append(future.result())

        show_info("运行结果:")
        show_info("=" * 40)
        success_count = 0
        for filename, success, output in results:
            if success:
                show_success(f"成功运行 {filename}")
                success_count += 1
            else:
                show_error(f"运行出错 {filename}")
            if output.strip():
                show_info(f"输出: {output.strip()}")
            show_info("=" * 40)
        show_success(f"完成运行 {success_count}/{len(valid_files)} 个文件")
    else:
        files = get_input_files([], allow_multiple=False)
        if not files:
            return

        selected_file = files[0]
        filename, success, output = run_script(selected_file)
        if success:
            show_success(f"成功运行了 {filename}")
        else:
            show_error(f"运行失败: {filename}")
        if output.strip():
            show_info(output.strip())


if __name__ == "__main__":
    main()
