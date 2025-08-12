from datetime import datetime
from threading import Thread, Lock
import time
import json
import os
import atexit
from flask import Flask, render_template, jsonify, request, send_file
import math
import random



from init import *

app = Flask(__name__)

# --- API Routes ---
@app.route('/api/angle/<int:channel>/<int:angle>', methods=["POST"])
def set_angle_for_servo(channel, angle):
    smooth_servo(channel, start=servo_angles.get(channel, 90), end=angle, steps=10, delay=0.01)
    return jsonify({"channel": channel, "angle": angle})

@app.route('/api/state')
def get_state():
    return jsonify(servo_angles)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/zero_pose', methods=["POST"])
def set_zero_pose(): 
    zero_pose()
    return jsonify({"status": "zero pose set"})

@app.route('/api/default_pose', methods=["POST"])
def set_default_pose(): 
    default_pose()
    return jsonify({"status": "default pose set"})

from test import *

    
# # # --- Start Server ---
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=False)



time.sleep(3)  # Allow time for the initial pose to settle
# --- Shutdown handler ---
def shutdown():
    print("🔻 Shutting down, releasing servos...")
    for servo in servos:
        pwm.setServoPulse(servo, 0)

atexit.register(shutdown) 