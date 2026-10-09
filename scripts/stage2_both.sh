#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/base64/files.json --script scripts/demo_stage2.txt
