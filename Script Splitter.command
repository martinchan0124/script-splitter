#!/bin/bash
DIR="/Users/martinchan/Documents/Work/2026SURF/Script Splitter"
cd "$DIR"
export PYTHONPATH="$DIR:$PYTHONPATH"
nohup python3 app/gui.py > /dev/null 2>&1 &
