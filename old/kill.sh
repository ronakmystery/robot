#!/bin/bash
echo "🛑 Stopping robot services..."

# Stop the systemd service
sudo systemctl stop robot.service 2>/dev/null

# Kill any stray Python processes
pkill -f manual_control.py
pkill -f camera_server.py
pkill -f btcontroller.py

# Release servos safely
python3 /home/x/robot/kill_servos.py

echo "✅ Robot services stopped and servos released."
