#!/bin/sh
set -eu
if [ "${1:-}" = "test" ]; then
    python3 -m unittest discover -s tests -v
else
    python3 -m src.shell "$@"
fi
