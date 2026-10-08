#!/bin/sh
# Этап 2: запуск эмулятора с путем к VFS и стартовым скриптом.
cd "$(dirname "$0")/.."
python3 -m src.shell --vfs vfs/minimal.json --script scripts/demo_stage2.txt
