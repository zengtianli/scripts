---
name: dev-raycast
description: Raycast 脚本开发规范。模板、命名、注意事项。当开发 Raycast 快捷脚本时触发。
---

# Raycast 脚本开发规范

> 📍 位置：`execute/raycast/`

## 目录结构

```
raycast/
├── app_*.py          ← 应用启动脚本
├── open_*.py         ← 打开文件/目录脚本
├── run_*.py          ← 运行命令脚本
└── *.sh              ← Shell 快捷脚本
```

## Python 脚本模板

```python
#!/Users/tianli/miniforge3/bin/python3

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title 脚本标题
# @raycast.mode silent

# Optional parameters:
# @raycast.icon 🚀
# @raycast.packageName 包名

import subprocess

def main():
    # 脚本逻辑
    pass

if __name__ == "__main__":
    main()
```

## 常用脚本类型

### 应用启动 (app_*.py)

```python
#!/Users/tianli/miniforge3/bin/python3

# @raycast.title Open Cursor
# @raycast.mode silent
# @raycast.icon 📝

import subprocess
subprocess.run(["open", "-a", "Cursor"])
```

### 打开目录 (open_*.py)

```python
#!/Users/tianli/miniforge3/bin/python3

# @raycast.title Open Downloads
# @raycast.mode silent
# @raycast.icon 📂

import subprocess
subprocess.run(["open", "/Users/tianli/Downloads"])
```

### 执行命令 (run_*.py)

```python
#!/Users/tianli/miniforge3/bin/python3

# @raycast.title Run Script
# @raycast.mode fullOutput
# @raycast.icon ⚡

import subprocess
result = subprocess.run(["python", "script.py"], capture_output=True, text=True)
print(result.stdout)
```

## 注意事项

1. **Shebang** - 必须使用完整 Python 路径：`#!/Users/tianli/miniforge3/bin/python3`
2. **权限** - 脚本需要可执行权限：`chmod +x script.py`
3. **模式** - `silent` 静默执行，`fullOutput` 显示输出
4. **图标** - 使用 emoji 或 SF Symbols
