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



def test(legs=all_legs,d1=0, d2=0, d3=0,speed=20):
    threads=[]
    for idx, leg in enumerate(legs.values()):
        a, b, c = leg
        symmetric_deg = 1
        if idx == 1 or idx == 2:
            symmetric_deg = -1
        if idx >= 2:
            symmetric_deg *= -1
        t= Thread(target=move_leg, args=(a, servo_angles[a]+(d1*symmetric_deg), b, servo_angles[b]+(d2*symmetric_deg), c, servo_angles[c]+(d3*symmetric_deg)), kwargs={"speed": speed})
        t.start()
        threads.append(t)
    for t in threads:
        t.join()


front_legs= {
    "front_left": (A[0], B[0], C[0]),
    "front_right": (A[1], B[1], C[1]),
}
back_legs = {
    "back_left": (A[2], B[2], C[2]),
    "back_right": (A[3], B[3], C[3]),
}

left_legs = {
    "front_left": (A[0], B[0], C[0]),
    "back_left": (A[2], B[2], C[2]),
}

right_legs = {
    "front_right": (A[1], B[1], C[1]),
    "back_right": (A[3], B[3], C[3]),
}

for i in range(2, 5):
    speed= random.randint(10, 80)
    threads = []
    t= Thread(target=test, kwargs={"legs": right_legs, "d1": 20, "d2": 0, "d3": 0, "speed": speed})  # Move front legs
    t.start()
    threads.append(t)
    t= Thread(target=test, kwargs={"legs": left_legs, "d1": 20, "d2": 0, "d3": 0, "speed": speed})  # Move back legs
    t.start()
    threads.append(t)
    
    for t in threads:
        t.join()

    test(legs=back_legs, d1=0, d2=60, d3=60, speed= speed)  # Move back legs

    threads = []
    t= Thread(target=test, kwargs={"legs": right_legs, "d1": -40, "d2": 0, "d3": 0, "speed": speed})  # Move front legs
    t.start()
    threads.append(t)
    t= Thread(target=test, kwargs={"legs": left_legs, "d1": -40, "d2": 0, "d3": 0, "speed": speed})  # Move back legs
    t.start()
    threads.append(t)
    
    for t in threads:
        t.join()

    test(legs=front_legs, d1=0, d2=60, d3=60, speed=speed)

    
    threads = []
    t= Thread(target=test, kwargs={"legs": right_legs, "d1": 20, "d2": 0, "d3": 0, "speed": speed})  # Move front legs
    t.start()
    threads.append(t)
    t= Thread(target=test, kwargs={"legs": left_legs, "d1": 20, "d2": 0, "d3": 0, "speed": speed})  # Move back legs
    t.start()
    threads.append(t)
    
    for t in threads:
        t.join()


    default_pose()  # Reset to default pose




# --- API Routes ---
@app.route('/api/angle/<int:channel>/<int:angle>', methods=["POST"])
def set_angle_for_servo(channel, angle):
    smooth_servo(channel, start=servo_angles.get(channel, 90), end=angle, steps=40, delay=0.01)
    return jsonify({"channel": channel, "angle": angle})

@app.route('/api/state')
def get_state():
    return jsonify(servo_angles)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/default_pose', methods=["POST"])
def set_default_pose(): 
    load_default_poses()
    return jsonify({"status": "default pose set"})




    
# # --- Start Server ---
# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000, debug=False)



save_servo_angles()  # Save initial angles at startup
# --- Shutdown handler ---
def shutdown():
    print("🔻 Shutting down, releasing servos...")
    for servo in servos:
        pwm.setServoPulse(servo, 0)
        time.sleep(.1)

atexit.register(shutdown) 