#!/bin/bash
# @raycast.schemaVersion 1
# @raycast.title xlsx-encode-duplicates
# @raycast.description Generate unique user codes for duplicate enterprise codes in Excel
# @raycast.mode fullOutput
# @raycast.icon 📊
# @raycast.packageName Scripts
source "$(dirname "$0")/../lib/run_python.sh" && run_python "data/xlsx_encode_duplicates.py" "$@"
