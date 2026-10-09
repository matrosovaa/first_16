#!/bin/sh
cd "$(dirname "$0")/.."

python3 -m src.shell --vfs vfs/base64/missing.json --script scripts/demo_stage3.txt
echo "exit code: $?"

python3 -m src.shell --vfs vfs/base64/invalid.json --script scripts/demo_stage3.txt
echo "exit code: $?"
