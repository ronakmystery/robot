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



legs = {
    "front_left": (A[0], B[0], C[0]),
    "front_right": (A[1], B[1], C[1]),
    "back_left": (A[2], B[2], C[2]),
    "back_right": (A[3], B[3], C[3]),
}


def move_leg(b, angle1, c, angle2):
    t1 = Thread(target=smooth_servo, kwargs={"servo": b, "start": servo_angles[b], "end": angle1})
    t2 = Thread(target=smooth_servo, kwargs={"servo": c, "start": servo_angles[c], "end": angle2})

    t1.start()
    t2.start()

    t1.join()
    t2.join()




threads=[]
for idx, leg in enumerate(legs.values()):
    for servo in leg:
        t = Thread(target=smooth_servo, kwargs={"servo": servo, "start": servo_angles.get(servo, offsets[servo]), "end": offsets[servo], "steps": 40, "delay": 0.01})
        t.start()
        threads.append(t)
for t in threads:
    t.join()


# for idx, leg in enumerate(legs.values()):
#     deg=20
#     a,b,c=leg
#     move_leg(b, servo_angles[b]+deg, c, servo_angles[c]+deg)
#     move_leg(b, servo_angles[b]-deg, c, servo_angles[c]-deg)







# def steps_for_degrees(degrees, step_resolution):
#     radians = math.radians(degrees)  # convert degrees to radians
#     return int(radians * step_resolution)

# # === EASING ===

# def linear(t):
#     return t

# def ease_in_out_sine(t):
#     return -(math.cos(math.pi * t) - 1) / 2

# # === 2D PATHS ===

# def path_circle(t, r, center):
#     x = center + r * math.cos(t)
#     y = center + r * math.sin(t)
#     return int(x), int(y)

# def path_ellipse(t, rx=30, ry=15, center=90):
#     x = center + rx * math.cos(t)
#     y = center + ry * math.sin(t)
#     return int(x), int(y)

# # === 2D LEG MOVEMENT ===
# def clockwise_leg(leg, step_res=30, radius=30, center=90, path_fn=path_ellipse, ease_fn=linear, phase=0.0):
#     a, b, c = leg
#     steps = steps_for_degrees(360, step_res)


#     for i in range(steps):
#         prog = i / steps
#         eased_prog = ease_fn(prog)
#         theta = -2 * math.pi * (eased_prog + phase)

#         x, y = path_fn(theta, radius, center)
#         move_leg(b, offsets[b] + (x - 90), c, offsets[c] + (y - 90))




# threads=[]
# for idx, leg in enumerate(legs.values()):
#     n=-20
#     if idx<2:
#         n*=-1
#     t = Thread(target=set_servo_angle, args=(leg[0], offsets[leg[0]]+n))
#     t.start()
#     threads.append(t)
# for t in threads:
#     t.join()



# total_loops = 5
# for i in range(total_loops):
#     step_res = 100
#     radius =30
#     center = 90
#     path_fn = path_circle
#     ease_fn = linear

#     base_phase = i  # this ensures each loop continues smoothly
#     threads = []
#     for idx, leg in enumerate(legs.values()):
#         leg_phase = base_phase + (idx % 2) * 4  # alternate left-right legs

#         t = Thread(target=clockwise_leg, args=(leg, step_res, radius, center, path_fn, ease_fn, leg_phase))
#         t.start()
#         threads.append(t)   

#     for t in threads:
#         t.join()

# load_default_poses()  # Reset to default pose after walking


# for _ in range(4):  # Walk 3 times
#     threads = gait_mode(rad=10, path=path_circle, ease=linear, steps=10)
#     for t in threads:
#         t.join()



# @app.route('/api/walk', methods=["POST"])
# def trigger_walk():
#     default_pose()  # Ensure we start from a known pose
#     time.sleep(1)
#     for _ in range(2):  # Walk 3 times
#         threads = gait_mode(rad=20, path=path_circle, ease=linear, steps=40)
#         for t in threads:
#             t.join()
#     pose_to_angles(poses["sit"])  # Ensure we return to a known pose after walking


# @app.route('/api/run', methods=["POST"])
# def trigger_run():
#     default_pose()  # Ensure we start from a known pose
#     time.sleep(1)
#     for _ in range(2):  # Run 3 times
#         threads = gait_mode(rad=20, path=path_circle, ease=linear, steps=20)
#         for t in threads:
#             t.join()

#     default_pose()  # Return to default pose after running
#     pose_to_angles(poses["stretch"])  # Ensure we return to a known pose after running


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




    
# --- Start Server ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)



save_servo_angles()  # Save initial angles at startup
# --- Shutdown handler ---
def shutdown():
    print("🔻 Shutting down, releasing servos...")
    for servo in servos:
        pwm.setServoPulse(servo, 0)
        time.sleep(.1)

atexit.register(shutdown) 