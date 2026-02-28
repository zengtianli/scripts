#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title tts-volcano
# @raycast.mode fullOutput
# @raycast.icon 🔊
# @raycast.packageName TTS
# @raycast.description 火山引擎语音合成（文本转语音）
# @raycast.argument1 { "type": "text", "placeholder": "输入要朗读的文本" }
source "$(dirname "$0")/../lib/run_python.sh" && run_python "tts_volcano.py" "$@"
