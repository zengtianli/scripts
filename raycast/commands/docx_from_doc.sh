#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title docx-from-doc
# @raycast.description Convert .doc files to .docx format
# @raycast.mode fullOutput
# @raycast.icon 📝
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "document/docx_from_doc.py" "$@"
