#!/bin/sh
cd "$(dirname "$0")/.."

python3 -m src.shell --script scripts/error_stage2.txt
echo "exit code: $?"

python3 -m src.shell --script scripts/missing.txt
echo "exit code: $?"
