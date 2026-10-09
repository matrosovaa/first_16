#!/bin/sh
cd "$(dirname "$0")/.."
printf 'ls\nexit\n' | python3 -m src.shell --vfs vfs/base64/minimal.json
