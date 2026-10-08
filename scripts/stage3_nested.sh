#!/bin/sh
# Этап 3: проверяем JSON-VFS с тремя уровнями.
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/nested.json --script scripts/demo_stage3.txt
