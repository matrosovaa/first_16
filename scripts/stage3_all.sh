#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/base64/files.json --script scripts/test_all.txt
echo "exit code: $?"
