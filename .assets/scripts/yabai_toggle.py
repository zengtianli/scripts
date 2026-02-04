#!/usr/bin/env python3
# @raycast.schemaVersion 1
# @raycast.title yabai-toggle
# @raycast.mode silent
# @raycast.icon 🪟

import subprocess
r = subprocess.run(['pgrep', '-x', 'yabai'], capture_output=True)
if r.returncode == 0:
    subprocess.run(['yabai', '--stop-service'])
else:
    subprocess.run(['yabai', '--start-service'])
