#!/bin/bash
cd /home/x/robot

# Start Flask server if not running
pgrep -f manual_control.py >/dev/null || /usr/bin/python3 /home/x/robot/manual_control.py &

# Start camera if not running
pgrep -f camera_server.py >/dev/null || /usr/bin/python3 /home/x/robot/sensors/camera_server.py &


# Start joystick controller in foreground
exec /usr/bin/python3 /home/x/robot/btcontroller.py
