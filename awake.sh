#!/bin/bash
cd /home/x/robot

# Start Flask server in background
/usr/bin/python3 /home/x/robot/manual_control.py &

# Small delay to make sure server is up
sleep 3

# Start joystick controller in foreground (systemd will track this)
exec /usr/bin/python3 /home/x/robot/btcontroller.py
