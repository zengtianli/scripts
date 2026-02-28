#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tts_volcano.py - 火山引擎大模型语音合成 TTS

用法：
  # Raycast 调用（通过 argument 输入文本）
  # 命令行
  python tts_volcano.py "你好，这是一段测试语音"
  python tts_volcano.py "文本" -o output.mp3
  python tts_volcano.py "文本" -v zh_female_shuangkuai_moon_bigtts
"""

import os
import sys
import json
import uuid
import gzip
import struct
import argparse
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))
from display import show_success, show_error, show_info
from file_ops import fatal_error

# ── 配置 ──────────────────────────────────────────────
APP_ID = os.environ.get("VOLCANO_APP_ID")
ACCESS_TOKEN = os.environ.get("VOLCANO_ACCESS_TOKEN")
CLUSTER = "volcano_tts"
VOICE_TYPE = "BV700_streaming"  # 灿灿（热门女声）
WS_URL = "wss://openspeech.bytedance.com/api/v1/tts/ws_binary"
# ─────────────────────────────────────────────────────


def build_request(text: str, voice: str = VOICE_TYPE) -> bytes:
    """构造二进制协议请求帧"""
    payload = json.dumps({
        "app": {"appid": APP_ID, "token": ACCESS_TOKEN, "cluster": CLUSTER},
        "user": {"uid": "local_user"},
        "audio": {
            "voice_type": voice,
            "encoding": "mp3",
            "speed_ratio": 1.0,
        },
        "request": {
            "reqid": str(uuid.uuid4()),
            "text": text,
            "operation": "query",
        },
    }).encode("utf-8")

    payload_compressed = gzip.compress(payload)

    header = bytearray(4)
    header[0] = 0x11  # version=1, header_size=1
    header[1] = 0x10  # msg_type=full_client(1), flags=0(no sequence)
    header[2] = 0x11  # serialization=json(1), compression=gzip(1)
    header[3] = 0x00  # reserved

    return bytes(header) + struct.pack(">I", len(payload_compressed)) + payload_compressed


def parse_response(data: bytes) -> tuple[int, bytes]:
    """解析服务端响应帧，返回 (message_type, payload)"""
    msg_type = (data[1] >> 4) & 0x0F
    compression = data[2] & 0x0F
    offset = 4

    if msg_type == 0x0B:  # audio-only response
        offset += 4  # sequence
        payload_size = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        return msg_type, data[offset:offset + payload_size]

    elif msg_type == 0x0F:  # error
        code = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        payload_size = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        payload = data[offset:offset + payload_size]
        if compression == 1:
            payload = gzip.decompress(payload)
        err = json.loads(payload)
        raise RuntimeError(f"TTS 错误 (code={code}): {err}")

    elif msg_type == 0x09:  # full-server response
        flags = data[1] & 0x0F
        if flags in (1, 2, 3):
            offset += 4
        payload_size = struct.unpack(">I", data[offset:offset + 4])[0]
        offset += 4
        payload = data[offset:offset + payload_size]
        if compression == 1:
            payload = gzip.decompress(payload)
        return msg_type, payload

    return msg_type, b""


def tts(text: str, output: str = "output.mp3", voice: str = VOICE_TYPE, play: bool = True):
    """文本转语音，保存为 mp3 并播放"""
    import websocket

    ws = websocket.create_connection(
        WS_URL,
        header={"Authorization": f"Bearer; {ACCESS_TOKEN}"},
    )
    ws.send_binary(build_request(text, voice))

    audio_chunks = []
    while True:
        _, data = ws.recv_data()
        if not data:
            break
        msg_type, payload = parse_response(data)
        if msg_type == 0x0B:  # audio data
            audio_chunks.append(payload)
            flags = data[1] & 0x0F
            if flags in (2, 3):
                break
        elif msg_type == 0x09:  # server response
            break
        elif msg_type == 0x0F:  # error
            break

    ws.close()

    if not audio_chunks:
        fatal_error("未收到音频数据")

    output_path = Path(output)
    output_path.write_bytes(b"".join(audio_chunks))
    show_success(f"已保存: {output_path} ({output_path.stat().st_size / 1024:.1f} KB)")

    if play:
        subprocess.run(["afplay", str(output_path)])


def main():
    if not APP_ID or not ACCESS_TOKEN:
        fatal_error("缺少环境变量 VOLCANO_APP_ID 或 VOLCANO_ACCESS_TOKEN，请在 env.zsh 中配置")

    # Raycast argument 模式：sys.argv[1] 是文本，无 flag
    if len(sys.argv) == 2 and not sys.argv[1].startswith("-"):
        text = sys.argv[1]
        try:
            tts(text)
        except Exception as e:
            fatal_error(f"语音合成失败: {e}")
        return

    parser = argparse.ArgumentParser(description="火山引擎 TTS")
    parser.add_argument("text", help="要合成的文本")
    parser.add_argument("-o", "--output", default="output.mp3", help="输出文件路径")
    parser.add_argument("-v", "--voice", default=VOICE_TYPE, help="音色")
    parser.add_argument("--no-play", action="store_true", help="不自动播放")
    args = parser.parse_args()

    try:
        tts(args.text, args.output, args.voice, play=not args.no_play)
    except Exception as e:
        fatal_error(f"语音合成失败: {e}")


if __name__ == "__main__":
    main()
