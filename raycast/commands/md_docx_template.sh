#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title md-to-docx-template
# @raycast.mode fullOutput
# @raycast.icon 📄
# @raycast.packageName DOCX
source "$(dirname "$0")/../lib/run_python.sh" && run_python "md_docx_template.py" "$@"
