#!/bin/bash
set -m
trap "kill 0" EXIT

pgrep -f manual_control.py >/dev/null || /usr/bin/python3 /home/x/robot/manual_control.py &
# pgrep -f btcontroller.py   >/dev/null || /usr/bin/python3 /home/x/robot/btcontroller.py &
# pgrep -f camera_server.py >/dev/null || /usr/bin/python3 /home/x/robot/sensors/camera_server.py &

wait

