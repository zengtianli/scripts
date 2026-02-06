#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title file-run
# @raycast.mode fullOutput
# @raycast.icon 🚀
# @raycast.packageName Files
# @raycast.description Run selected shell or python scripts
# @raycast.argument1 { "type": "dropdown", "placeholder": "Mode", "data": [{"title": "Single", "value": "single"}, {"title": "Parallel", "value": "parallel"}] }

import subprocess
import os
import stat
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

import shutil

PYTHON_PATH = shutil.which("python3") or "python3"

def get_finder_selection(multiple=False):
    """获取 Finder 选中的文件"""
    if multiple:
        script = '''
        tell application "Finder"
            set sel to selection
            set paths to {}
            repeat with f in sel
                set end of paths to POSIX path of (f as alias)
            end repeat
            set AppleScript's text item delimiters to ","
            return paths as text
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        paths = result.stdout.strip()
        return [p.strip() for p in paths.split(',') if p.strip()] if paths else []
    else:
        script = '''
        tell application "Finder"
            set sel to selection
            if (count of sel) > 0 then
                return POSIX path of (item 1 of sel as alias)
            end if
        end tell
        '''
        result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
        return result.stdout.strip()

def run_script(file_path):
    """运行单个脚本"""
    file_ext = os.path.splitext(file_path)[1].lower()
    filename = os.path.basename(file_path)
    script_dir = os.path.dirname(file_path)

    if file_ext not in ['.sh', '.py']:
        return filename, False, "不是 shell 脚本或 python 文件"

    if file_ext == '.sh':
        st = os.stat(file_path)
        if not (st.st_mode & stat.S_IXUSR):
            os.chmod(file_path, st.st_mode | stat.S_IXUSR)

    try:
        if file_ext == '.py':
            result = subprocess.run([PYTHON_PATH, file_path], capture_output=True, text=True, cwd=script_dir, timeout=300)
        else:
            result = subprocess.run([file_path], capture_output=True, text=True, cwd=script_dir, shell=True, timeout=300)
        output = result.stdout + result.stderr
        return filename, result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return filename, False, "运行超时（5分钟）"
    except Exception as e:
        return filename, False, str(e)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "single"

    if mode == "parallel":
        files = get_finder_selection(multiple=True)
        if not files:
            print("❌ 没有在 Finder 中选择文件")
            return

        valid_files = [f for f in files if os.path.splitext(f)[1].lower() in ['.sh', '.py']]
        if not valid_files:
            print("❌ 没有选中的 shell 脚本或 python 文件")
            return

        print(f"⏳ 开始并行运行 {len(valid_files)}/{len(files)} 个文件...")
        print("")

        results = []
        with ThreadPoolExecutor(max_workers=min(len(valid_files), 4)) as executor:
            futures = {executor.submit(run_script, f): f for f in valid_files}
            for future in as_completed(futures):
                results.append(future.result())

        print("📊 运行结果:")
        print("=" * 40)
        success_count = 0
        for filename, success, output in results:
            if success:
                print(f"✅ 成功运行 {filename}")
                success_count += 1
            else:
                print(f"❌ 运行出错 {filename}")
            if output.strip():
                print(f"输出: {output.strip()}")
            print("=" * 40)
        print(f"\n✅ 完成运行 {success_count}/{len(valid_files)} 个文件")
    else:
        selected_file = get_finder_selection(multiple=False)
        if not selected_file:
            print("❌ 没有在 Finder 中选择文件")
            return

        filename, success, output = run_script(selected_file)
        if success:
            print(f"✅ 成功运行了 {filename}")
        else:
            print(f"❌ 运行失败: {filename}")
        if output.strip():
            print(output.strip())

if __name__ == '__main__':
    main()
