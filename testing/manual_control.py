from flask import Flask, request, jsonify
import threading, time, math

from servos import *
from poses import *

app = Flask(__name__)

# --- State ---
MODE = "stop"          # "walk" or "stop"
WALK_TYPE = "default"  # gait profile name
BACKWARDS = False
LATERAL = 0            # hip offset
HEIGHT_UP = 0          # right trigger
HEIGHT_DOWN = 0        # left trigger
PITCH_UP = 0           # stick back (nose up)
PITCH_DOWN = 0         # stick forward (nose down)

baseline = default.copy()   # ✅ robot pose starts at default
balance_offset = {ch: 0.0 for ch in baseline}

set_targets(baseline)

# --- Gait profiles ---
def walking_speed(mode="precision"):
    profiles = {
        "carpet_fast":   (40,3),
        "carpet_slow":   (20, 3),
        "hard_fast":     (25, 3),
        "hard_slow":     (15, 1.5),
        "grass":         (35, 2),
        "rocky":         (20, 1),
        "sand":          (45, 1.5),
        "precision":     (10, 1),
        "creep":         (15, 0.5),
        "bound":         (50, 2.5),
        "trot":          (35, 2.5),
        "run":           (45, 3.5),
        "default":       (20, 2)
    }
    return profiles.get(mode, profiles["precision"])

# --- Gait math ---
def circle_x(t, amp=40, freq=1.0, phase=0):
    return amp * math.cos(2 * math.pi * freq * t + phase)

def circle_y(t, amp=40, freq=1.0, phase=0):
    return amp * math.sin(2 * math.pi * freq * t + phase)

LEG_MAP = [(0,1,2,+1),(4,5,6,+1),(8,9,10,-1),(12,13,14,-1)]


# --- Balance thread ---
from sensors.imu import get_roll_pitch_angles

def balance_loop():
    global baseline, balance_offset
    recover = False
    while True:
        roll, pitch = get_roll_pitch_angles()  # degrees
        scale = 4  # tune this

        # Emergency protect override
        if abs(roll) > 40 or abs(pitch) > 40:
            baseline = protect   # ✅ switch to protect pose
            balance_offset = {ch: 0.0 for ch in baseline}
            recover = True
        else:
            if recover:
                if abs(roll) < 5 and abs(pitch) < 5:
                    baseline = default   # ✅ back to default
                    balance_offset = {ch: 0.0 for ch in baseline}
                    recover = False

            # Roll dominates → left/right tilt correction
            if abs(roll) > abs(pitch):
                balance_offset.update({
                    1: -roll * scale,
                    5: -roll * scale,
                    9:  roll * scale,
                    13: roll * scale,

                    2: -roll * scale,
                    6: -roll * scale,
                    10: roll * scale,
                    14: roll * scale,
                })
            else:
                # Pitch dominates → forward/back tilt correction
                balance_offset.update({
                    1:  pitch * scale,
                    5: -pitch * scale,
                    9: -pitch * scale,
                    13: pitch * scale,

                    2:  pitch * scale,
                    6: -pitch * scale,
                    10:-pitch * scale,
                    14: pitch * scale,
                })

        time.sleep(0.01)

def start_balance_thread():
    threading.Thread(target=balance_loop, daemon=True).start()


# --- Gait updater ---
def update_legs(x, y, backwards=False, lateral=0,
                height_up=0, height_down=0,
                pitch_up=0, pitch_down=0):
    global baseline
    cmds = {}
    for a, b, c, ysign in LEG_MAP:
        x_val = x if backwards else -x
        y_val = ysign * y

        # hips (lateral shift)
        cmds[a] = baseline[a] - lateral   # ✅ use baseline

        # stride + lift base
        stride_val = baseline[b] + x_val  # ✅ use baseline
        lift_val   = baseline[c] + y_val  # ✅ use baseline

        # --- Apply trigger offsets ---
        if a in (4, 8):   # right legs
            stride_val -= height_up * ysign
            lift_val   -= height_up * ysign
        elif a in (0, 12):  # left legs
            stride_val += height_down * ysign
            lift_val   += height_down * ysign

        # --- Apply pitch offsets (front + back, mirrored/inverted) ---
        if a == 0:   # front-left
            stride_val -= pitch_down
            lift_val   -= pitch_down
            stride_val += pitch_up
            lift_val   += pitch_up

        elif a == 4:  # front-right (mirrored)
            stride_val += pitch_down
            lift_val   += pitch_down
            stride_val -= pitch_up
            lift_val   -= pitch_up

        elif a == 12:  # back-left (inverted like FL)
            stride_val += pitch_down
            lift_val   += pitch_down
            stride_val -= pitch_up
            lift_val   -= pitch_up

        elif a == 8:   # back-right (inverted like FR)
            stride_val -= pitch_down
            lift_val   -= pitch_down
            stride_val += pitch_up
            lift_val   += pitch_up

        # --- Apply balance offsets (IMU correction) ---
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
            amp, freq = walking_speed(WALK_TYPE)
            x = circle_x(t, amp=amp, freq=freq)
            y = circle_y(t, amp=amp, freq=freq)
        else:
            x, y = 0, 0

        update_legs(
            x, y,
            backwards=BACKWARDS,
            lateral=LATERAL,
            height_up=HEIGHT_UP,
            height_down=HEIGHT_DOWN,
            pitch_up=PITCH_UP,
            pitch_down=PITCH_DOWN
        )

        time.sleep(0.02)

threading.Thread(target=walking_loop, daemon=True).start()


# --- API ---
@app.route("/api/state")
def get_state():
    return jsonify({
        "mode": MODE,
        "walk_type": WALK_TYPE,
        "backwards": BACKWARDS,
        "lateral": LATERAL,
        "height_up": HEIGHT_UP,
        "height_down": HEIGHT_DOWN,
        "pitch_up": PITCH_UP,
        "pitch_down": PITCH_DOWN
    })

@app.route("/api/walk", methods=["POST"])
def set_walk():
    global MODE, WALK_TYPE, BACKWARDS, LATERAL, HEIGHT_UP, HEIGHT_DOWN, PITCH_UP, PITCH_DOWN
    data = request.get_json()
    if not data:
        return jsonify({"error":"no data"}),400

    if "mode" in data and data["mode"] in ["walk","stop"]:
        MODE = data["mode"]
    if "walk_type" in data:
        WALK_TYPE = data["walk_type"]
    if "backwards" in data:
        BACKWARDS = bool(data["backwards"])
    if "lateral" in data:
        try:
            LATERAL = int(data["lateral"])
        except:
            LATERAL = 0
    if "height_up" in data:
        try:
            HEIGHT_UP = int(data["height_up"])
        except:
            HEIGHT_UP = 0
    if "height_down" in data:
        try:
            HEIGHT_DOWN = int(data["height_down"])
        except:
            HEIGHT_DOWN = 0
    if "pitch_up" in data:
        try:
            PITCH_UP = int(data["pitch_up"])
        except:
            PITCH_UP = 0
    if "pitch_down" in data:
        try:
            PITCH_DOWN = int(data["pitch_down"])
        except:
            PITCH_DOWN = 0

    return jsonify({
        "status": "ok",
        "mode": MODE,
        "walk_type": WALK_TYPE,
        "backwards": BACKWARDS,
        "lateral": LATERAL,
        "height_up": HEIGHT_UP,
        "height_down": HEIGHT_DOWN,
        "pitch_up": PITCH_UP,
        "pitch_down": PITCH_DOWN
    })


# --- Main ---
if __name__ == "__main__":
    # start_balance_thread()
    print("🚀 Walking + Balance Server running at http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
