#!/bin/bash
DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$DIR"
export PYTHONPATH="$DIR:$PYTHONPATH"
nohup python3 app/gui.py > /dev/null 2>&1 &
