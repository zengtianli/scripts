#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title yabai-next
# @raycast.mode silent
# @raycast.icon 🪟

import subprocess
subprocess.run(['yabai', '-m', 'window', '--focus', 'next']) or subprocess.run(['yabai', '-m', 'window', '--focus', 'first'])
