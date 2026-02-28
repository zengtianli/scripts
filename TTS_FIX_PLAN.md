# Raycast 脚本环境问题修复方案

## 背景

在将 `tts_volcano.py` 集成到项目时，暴露了两个底层问题。这两个问题不是 TTS 脚本独有的，而是所有通过 Raycast 调用的脚本都可能遇到的。

## 问题一：Raycast 不继承 shell 环境变量

### 根因

用户的 API Key 等凭证统一配置在 `~/Documents/sync/zsh/config/env.zsh`，通过 `~/.zshrc` 加载。终端里一切正常，但 Raycast 启动脚本时不会 source zshrc，导致所有环境变量丢失。

### 影响范围

| 脚本 | 需要的环境变量 | 调用方式 | 缺失时行为 |
|------|--------------|---------|-----------|
| `tts_volcano.py` | `VOLCANO_APP_ID`, `VOLCANO_ACCESS_TOKEN` | Raycast → Python 符号链接 | `fatal_error` 退出 |
| `geocode/app.py` | `AMAP_API_KEY` | Raycast → Shell 包装 → Streamlit | UI 警告，可手动输入补救 |
| `geocode/run.py` | `AMAP_API_KEY` | CLI | `sys.exit(1)` |
| `geocode/src/geocode_by_address.py` | `AMAP_API_KEY` | CLI | 可用命令行参数补救 |
| `geocode/src/reverse_geocode.py` | `AMAP_API_KEY` | CLI | 同上 |
| `geocode/src/search_by_company.py` | `AMAP_API_KEY` | CLI | 同上 |
| `geocode/batch_company_geocode.py` | `AMAP_API_KEY` | CLI | 同上 |

不需要处理的：
- `qgis_util.py` 的 `HUAXI_DATA_DIR`：已有三层降级策略（环境变量 → 项目路径 → 工作目录）
- `irrigation/webapp/run.py` 的 `IRRIGATION_OUTPUT_DIR`：脚本内部自行设置

### 当前的临时补丁（需要移除）

`tts_volcano.py` 里有一个 `_load_env()` 私有函数，直接在脚本内解析 env.zsh。这是治标不治本的做法，不可复用。

### 修复方案

在公共库 `.assets/lib/env.py` 中新增 `load_env()` 函数：

```python
ENV_ZSH = Path.home() / "Documents/sync/zsh/config/env.zsh"

def load_env():
    """
    加载 env.zsh 中的环境变量。
    Raycast 不继承 shell 环境，需要主动加载。
    终端下环境变量已存在，setdefault 不会覆盖。
    """
    if not ENV_ZSH.exists():
        return
    import re
    for line in ENV_ZSH.read_text().splitlines():
        m = re.match(r'export (\w+)="([^"]*)"', line)
        if m:
            os.environ.setdefault(m.group(1), m.group(2))
```

然后在需要环境变量的脚本入口处调用：

```python
from env import load_env
load_env()
```

对于 Shell 包装脚本（`raycast/hydraulic/hy_geocode.sh` 等），在脚本头部加一行：

```bash
source "$HOME/Documents/sync/zsh/config/env.zsh"
```

### 具体操作清单

1. **编辑** `.assets/lib/env.py` — 追加 `load_env()` 函数
2. **编辑** `.assets/scripts/tts_volcano.py` — 删除 `_load_env()` 私有函数，改为 `from env import load_env; load_env()`
3. **编辑** `raycast/hydraulic/hy_geocode.sh` — 头部加 `source "$HOME/Documents/sync/zsh/config/env.zsh"`
4. **检查** `raycast/hydraulic/` 下其他 Shell 包装脚本是否也需要加（如果它们调用的项目也依赖环境变量）
5. **geocode 的 Python 文件暂不改动** — 它们通过 Shell 包装脚本调用，Shell 层 source env.zsh 后环境变量自然可用

---

## 问题二：Raycast 解析到系统 Python，找不到第三方包

### 根因

项目 shebang 统一为 `#!/usr/bin/env python3`。终端里 `env python3` 解析到 miniforge（因为 PATH 里 miniforge 在前），但 Raycast 的 PATH 不包含 miniforge，解析到系统 `/usr/bin/python3`，该 Python 没有 `websocket-client` 等第三方包。

### 当前的临时补丁（需要移除）

`tts_volcano.py` 的 shebang 被改成了 `#!/Users/tianli/miniforge3/bin/python3`（绝对路径），破坏了项目统一范式。

### 影响范围

当前只有 `tts_volcano.py` 受影响（它 import websocket）。但未来任何通过 Raycast 直接调用的 Python 脚本，只要用了非标准库的包，都会遇到同样问题。

Shell 包装脚本调用的 Streamlit 项目不受影响 — `streamlit` 命令本身就在 miniforge 的 bin 里，能找到正确的 Python。

### 修复方案：Raycast 配置 PATH（方案 A）

在 Raycast 中配置 Script Commands 的 PATH，使其包含 miniforge：

> Raycast → Settings → Extensions → Script Commands → PATH

添加 `/Users/tianli/miniforge3/bin` 到 PATH 前面。

**为什么选这个方案：**
- Raycast 官方推荐的做法
- 一次配置，所有脚本生效，未来新增脚本也不用操心
- 不侵入代码，不硬编码路径
- 不会因 Python 版本升级而失效

**备选方案（不推荐）：** 在脚本里加 `sys.path.insert(0, "/Users/tianli/miniforge3/lib/python3.12/site-packages")`。侵入性强，Python 3.12 → 3.13 时路径失效，每个脚本都要加。

### 具体操作清单

1. **Raycast 设置** — Script Commands 的 PATH 加入 `/Users/tianli/miniforge3/bin`（手动操作）
2. **编辑** `.assets/scripts/tts_volcano.py` — shebang 恢复为 `#!/usr/bin/env python3`
3. **编辑** `.assets/scripts/gantt_timeline.py` — 补上缺失的 `#!/usr/bin/env python3`（历史遗留，顺手修）

---

## 问题三：shebang 不统一（附带修复）

### 现状

| 范围 | 数量 | shebang | 状态 |
|------|------|---------|------|
| `.assets/lib/*.py` | 17 | `#!/usr/bin/env python3` | ✅ 统一 |
| `.assets/scripts/*.py`（除下面两个） | 35 | `#!/usr/bin/env python3` | ✅ 统一 |
| `.assets/scripts/tts_volcano.py` | 1 | `#!/Users/tianli/miniforge3/bin/python3` | ❌ 上次改坏 |
| `.assets/scripts/gantt_timeline.py` | 1 | 缺失 | ❌ 历史遗留 |

### 修复

已包含在问题二的操作清单中。

---

## 执行顺序

1. Raycast 手动配置 PATH（问题二，前置条件）
2. 编辑 `.assets/lib/env.py`，追加 `load_env()`（问题一）
3. 改造 `.assets/scripts/tts_volcano.py`：恢复 shebang + 删除 `_load_env()` + 改用公共库（问题一 + 二 + 三）
4. 修复 `.assets/scripts/gantt_timeline.py` shebang（问题三）
5. 编辑 `raycast/hydraulic/hy_*.sh`，头部 source env.zsh（问题一）
6. 验证：Raycast 中测试 tts-volcano 和地理编码工具

## 验证清单

- [ ] `echo $VOLCANO_APP_ID` 在 Raycast 脚本中有值
- [ ] Raycast 搜索 "tts-volcano"，输入文本，正常合成播放
- [ ] Raycast 搜索 "地理编码工具"，Streamlit 启动后 API Key 自动填充
- [ ] 终端 `python .assets/scripts/tts_volcano.py "测试"` 正常工作
- [ ] `grep -r '#!/' .assets/scripts/*.py | grep -v 'env python3'` 无输出（shebang 全部统一）
