#!/bin/sh
# Этап 5: chmod на VFS с несколькими уровнями.
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/project.json --script scripts/demo_stage5.txt
