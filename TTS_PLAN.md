# TTS 语音合成方案对比

## 需求场景

个人脚本使用，将文本朗读为语音。要求性价比高、中文支持好。

---

## 方案总览

| 方案 | 价格 | 中文质量 | 延迟 | 是否需要 API Key | 备注 |
|------|------|----------|------|-------------------|------|
| **edge-tts** | 免费 | ★★★★☆ | ~1s | 否 | 微软 Edge 在线服务 |
| **Kokoro-82M** | 免费 | ★★★☆☆ | 本地推理 | 否 | 开源本地模型，82M 参数 |
| **OpenAI TTS** | $15/百万字符 | ★★★★☆ | ~1-2s | 是 | 质量稳定，6 种音色 |
| **gpt-4o-mini-tts** | ~$0.6/百万 token | ★★★★★ | ~1-2s | 是 | 最新，支持情感指令 |
| **Fish Speech** | 免费(本地) / API 付费 | ★★★★★ | 本地推理 | 否(本地) | 开源，中文顶级 |
| **火山引擎** | 免费额度 + 按量 | ★★★★★ | ~0.5s | 是 | ✅ 已接入 · 字节跳动，中文最强之一 |
| **Deepgram Aura-2** | $30/百万字符 | ★★☆☆☆ | <200ms | 是 | 英文极快，中文弱 |
| **ElevenLabs** | ~$5/月起 | ★★★☆☆ | ~1s | 是 | 英文最自然，贵 |

---

## 推荐方案详解

### 🥇 首选：edge-tts（免费 + 好用）

- **价格**：完全免费，无需 API Key，无调用限制
- **原理**：调用微软 Edge 浏览器的在线 TTS 服务（WebSocket 协议）
- **中文音色**：`zh-CN-XiaoxiaoNeural`（女）、`zh-CN-YunxiNeural`（男）等 10+ 种
- **安装**：`pip install edge-tts`
- **输出格式**：MP3
- **缺点**：依赖网络；微软可能随时调整接口（但已稳定运行多年）

```python
import asyncio
import edge_tts

async def tts(text, output_file="output.mp3", voice="zh-CN-XiaoxiaoNeural"):
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_file)

asyncio.run(tts("你好，这是一段测试语音"))
```

命令行直接用：
```bash
edge-tts --text "你好世界" --voice zh-CN-YunxiNeural --write-media output.mp3
# 播放
afplay output.mp3
```

### 🥈 备选：OpenAI gpt-4o-mini-tts（付费但最灵活）

- **价格**：输入 $0.60/百万 token，输出 $12/百万 token（音频）
- **优势**：支持情感/风格指令（如"用温柔的语气朗读"），13 种音色
- **中文**：质量好，但不如国产方案地道
- **需要**：OpenAI API Key

```python
from openai import OpenAI

client = OpenAI()
response = client.audio.speech.create(
    model="gpt-4o-mini-tts",
    voice="coral",
    input="你好，这是一段测试语音",
    instructions="用自然、温和的语气朗读"
)
response.stream_to_file("output.mp3")
```

### 🥉 进阶：Fish Speech / OpenAudio（开源本地，中文顶级）

- **价格**：本地部署免费（Apache 2.0），云 API 约 $0.009/次
- **优势**：100 万小时训练数据，中日英多语言，支持声音克隆
- **缺点**：本地部署需要 GPU（推荐 4GB+ VRAM），模型较大
- **适合**：对中文质量要求极高、需要离线使用的场景

---

## 性价比结论

| 场景 | 推荐 | 理由 |
|------|------|------|
| 日常朗读、脚本自动化 | **edge-tts** | 免费、中文好、零配置 |
| 需要情感控制/高级指令 | **gpt-4o-mini-tts** | 灵活，已有 OpenAI Key 则成本极低 |
| 中文质量极致要求 | **Fish Speech** 本地 | 开源免费，中文最强 |
| 不想依赖网络 | **Kokoro-82M** | 82M 小模型，CPU 可跑 |

**我的建议**：先用 edge-tts，免费且中文质量够用。如果后续需要更自然的效果或情感控制，再切换到 gpt-4o-mini-tts。

---

## 参考来源

- [edge-tts PyPI](https://pypi.org/project/edge-tts/)
- [edge-tts GitHub](https://github.com/rany2/edge-tts)
- [OpenAI TTS 定价](https://costgoat.com/pricing/openai-tts)
- [Fish Speech GitHub](https://github.com/fishaudio/fish-speech)
- [Kokoro-82M HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M)
- [2025 TTS 横评](https://github.com/ruanyf/weekly/issues/7753)
- [Deepgram Aura-2](https://deepgram.com/product/text-to-speech/)

---

## 已接入：火山引擎 TTS

脚本位置：`.assets/scripts/tts_volcano.py`
Raycast 入口：`raycast/tts/tts_volcano.py`（符号链接）

使用方式：
```bash
# Raycast 搜索 "tts-volcano"，输入文本即可朗读
# 命令行
python .assets/scripts/tts_volcano.py "你好世界"
python .assets/scripts/tts_volcano.py "文本" -o output.mp3
python .assets/scripts/tts_volcano.py "文本" -v BV700_streaming --no-play
```

环境变量（已配置在 `env.zsh`）：
- `VOLCANO_APP_ID`
- `VOLCANO_ACCESS_TOKEN`
