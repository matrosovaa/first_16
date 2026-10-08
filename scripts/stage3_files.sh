#!/bin/sh
# Этап 3: проверяем VFS с несколькими файлами.
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/files.json --script scripts/demo_stage3.txt
