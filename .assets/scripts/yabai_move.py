#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title yabai-move
# @raycast.mode silent
# @raycast.icon 🪟
# @raycast.argument1 { "type": "text", "placeholder": "space (1-9)" }

import sys, subprocess
space = sys.argv[1] if len(sys.argv) > 1 else "1"
subprocess.run(["yabai", "-m", "window", "--space", space])
