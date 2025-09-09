from flask import Flask, request, jsonify
import threading, time, math

from servos import *
from poses import *

app = Flask(__name__)

# --- State ---
MODE = "stop"          # "walk" or "stop"
WALK_TYPE = "flat"
BACKWARDS = False
LATERAL = 0
HEIGHT = 0             # unified height
PITCH = 0              # unified pitch (signed: -100..100)
ROLL = 0               # unified roll (signed: -100..100)
SPEED = 0             # default speed

baseline = pose_protect.copy()
balance_offset = {ch: 0.0 for ch in baseline}
set_targets(baseline)



# --- Gait math ---
def circle_x(t, amp=40, freq=1.0, phase=0):
    return amp * math.cos(2 * math.pi * freq * t + phase)

def circle_y(t, amp=40, freq=1.0, phase=0):
    return amp * math.sin(2 * math.pi * freq * t + phase)

LEG_MAP = [(0,1,2,+1),(4,5,6,+1),(8,9,10,-1),(12,13,14,-1)]

# # --- Balance thread ---
from sensors.imu import get_roll_pitch_angles

def balance_loop():
    global baseline, balance_offset
    recover = False
    while True:
        roll, pitch = get_roll_pitch_angles()
        pitch=-pitch
        scale = 4
        if abs(roll) > 40 or abs(pitch) > 40:
            baseline = pose_protect
            balance_offset = {ch: 0.0 for ch in baseline}
            recover = True
        else:
            if recover and abs(roll) < 5 and abs(pitch) < 5:
                baseline = pose_default
                balance_offset = {ch: 0.0 for ch in baseline}
                recover = False

            if abs(roll) > abs(pitch):
                balance_offset.update({
                    1: -roll * scale, 5: -roll * scale,
                    9:  roll * scale, 13: roll * scale,
                    2: -roll * scale, 6: -roll * scale,
                    10: roll * scale, 14: roll * scale,
                })
            else:
                balance_offset.update({
                    1:  pitch * scale, 5: -pitch * scale,
                    9: -pitch * scale, 13: pitch * scale,
                    2:  pitch * scale, 6: -pitch * scale,
                    10:-pitch * scale, 14: pitch * scale,
                })
        time.sleep(0.01)

def start_balance_thread(): 
    threading.Thread(target=balance_loop, daemon=True).start()


# --- Gait updater ---
def update_legs(x, y, backwards=False, lateral=0, height=0, pitch=0, roll=0):
    global baseline
    cmds = {}
    
    for a, b, c, ysign in LEG_MAP:
        x_val = x if backwards else -x
        y_val = ysign * y

        # Hip (lateral only)
        if a in [0,4]:  # hip channels
            cmds[a] = baseline[a] - lateral*.5
        if a in [8,12]:  # hip channels
            cmds[a] = baseline[a] - lateral*.5

        # Stride + lift
        stride_val = baseline[b] + x_val
        lift_val   = baseline[c] + y_val


        #height adjustment
        if b and c in [1,2,13,14]:  # front legs
            stride_val += height*ysign
            lift_val += height*ysign
        if b and c in [5,6,9,10]:  # back legs
            stride_val -= height*ysign
            lift_val -= height*ysign

        
        
        
        # --- Apply pitch: front vs back legs ---
        if a in [0]:
            lift_val += pitch
        if a in [4]:  # back hips → apply opposite pitch
            lift_val -= pitch
        if b in [1]:
            stride_val += pitch
        if b in [5]:  # back hips → apply opposite pitch
            stride_val -= pitch

        # --- Apply roll: front-left leg only ---
        if a in [0]:   # front-left hip
            lift_val += roll
        if b in [1]:   # front-left stride
            stride_val += roll
        if a in [4]:   # front-left stride
            lift_val += roll
        if b in [5]:   # front-left stride
            stride_val += roll

        if a in [8]:   # back-right hip
            lift_val -= roll
        if b in [9]:   # back-right stride  
            stride_val -= roll
        if a in [12]:  # back-right hip
            lift_val -= roll
        if b in [13]:  # back-right stride
            stride_val -= roll




        # --- Apply balance correction only when idle ---
        if MODE == "stop":
            stride_val += balance_offset.get(b, 0)
            lift_val   += balance_offset.get(c, 0)

        cmds[b] = stride_val
        cmds[c] = lift_val

    set_targets(cmds)

# --- Background loop ---
def walking_loop():
    t0 = time.time()
    while True:
        t = time.time() - t0
        if MODE == "walk":
            amp=0+SPEED
            freq=4
            x = circle_x(t, amp=amp, freq=freq)
            y = circle_y(t, amp=amp, freq=freq)
        else:
            x, y = 0, 0

        update_legs(
            x, y,
            backwards=BACKWARDS,
            lateral=LATERAL,
            height=HEIGHT,
            pitch=PITCH,
            roll=ROLL
        )
        time.sleep(0.02)

threading.Thread(target=walking_loop, daemon=True).start()

@app.route("/api/walk", methods=["POST"])
def set_walk():
    global MODE, WALK_TYPE, BACKWARDS, LATERAL, HEIGHT, PITCH, ROLL, SPEED  
    global  baseline, balance_offset
    data = request.get_json()

    if "pause" in data and data["pause"]:
        MODE = "stop"
        baseline = pose_protect
        balance_offset = {ch: 0.0 for ch in baseline}
        def do_pause_pose():
            set_targets(pose_protect)
            time.sleep(1)

        threading.Thread(target=do_pause_pose, daemon=True).start()
        return jsonify({"status": "paused"}), 200

    if "start" in data and data["start"]:
        MODE = "stop"
        baseline = pose_default
        balance_offset = {ch: 0.0 for ch in baseline}
        def do_start_pose():
            set_targets(pose_default)
            time.sleep(1)

        threading.Thread(target=do_start_pose, daemon=True).start()

    if not data:
        return jsonify({"error":"no data"}),400

    if "mode" in data and data["mode"] in ["walk","stop"]:
        MODE = data["mode"]
    if "walk_type" in data: WALK_TYPE = data["walk_type"]
    if "backwards" in data: BACKWARDS = bool(data["backwards"])
    if "lateral" in data:   LATERAL = int(data.get("lateral",0))
    if "height" in data:    HEIGHT = int(data.get("height",0))
    if "pitch" in data:     PITCH = int(data.get("pitch",0))  # ✅ update pitch
    if "roll" in data:      ROLL = int(data.get("roll",0))   # ✅ update roll
    if "speed" in data:     SPEED = int(data.get("speed",0)) # ✅ update speed
    return jsonify({"status":"ok"}),200

import signal, sys
def shutdown_handler(sig, frame):
    print("\n🛑 Caught Ctrl+C, shutting down...")
    sys.exit(0)
signal.signal(signal.SIGINT, shutdown_handler)

# --- Main ---
if __name__ == "__main__":
    start_balance_thread()
    print("🚀 Walking + Balance Server running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)