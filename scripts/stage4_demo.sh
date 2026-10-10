#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/project.json --script scripts/demo_stage4.txt
