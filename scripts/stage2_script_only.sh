#!/bin/sh
cd "$(dirname "$0")/.."
python3 -m src.shell --script scripts/demo_stage2.txt
