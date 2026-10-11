#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/base64/project.json --script scripts/test_stage5.txt
echo "exit code: $?"
