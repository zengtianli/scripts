#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title yabai-prev
# @raycast.mode silent
# @raycast.icon 🪟

import subprocess
subprocess.run(['yabai', '-m', 'window', '--focus', 'prev']) or subprocess.run(['yabai', '-m', 'window', '--focus', 'last'])
