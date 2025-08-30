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


def angles_90():
    # Assuming this function sets the robot to a 90-degree pose
    for servo in servos:
        set_servo_angle(servo, 90)


# angles_90()


from init import *

app = Flask(__name__)

# --- API Routes ---
@app.route('/api/angle/<int:channel>/<int:angle>', methods=["POST"])
def set_angle_for_servo(channel, angle):
    set_servo_angle(channel, angle)
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

# # --- Start Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
