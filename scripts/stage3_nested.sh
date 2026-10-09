#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/base64/nested.json --script scripts/demo_stage3.txt
