#!/usr/bin/env python3

import subprocess
r = subprocess.run(['pgrep', '-x', 'yabai'], capture_output=True)
if r.returncode == 0:
    subprocess.run(['yabai', '--stop-service'])
    print("✅ yabai stopped")
else:
    subprocess.run(['yabai', '--start-service'])
    print("✅ yabai started")
