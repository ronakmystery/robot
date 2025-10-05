import socket, json, threading, time, math, sys, signal

from servos import set_targets,kill 
from poses import pose_default, pose_protect
from imu import get_roll_pitch_angles

# --- State ---
MODE = "stop"          # "walk" or "stop"
WALK_TYPE = "flat"
BACKWARDS = False
LATERAL = 0
HEIGHT = 0
PITCH = 0              # signed: -100..100
ROLL = 0               # signed: -100..100
SPEED = 0

baseline = pose_protect.copy()
balance_offset = {ch: 0.0 for ch in baseline}
set_targets(baseline)

# --- UDP Setup ---
UDP_IP = "0.0.0.0"
UDP_PORT = 5005
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# --- Gait math ---
def circle_x(t, amp=40, freq=1.0, phase=0):
    return amp * math.cos(2 * math.pi * freq * t + phase)

def circle_y(t, amp=40, freq=1.0, phase=0):
    return amp * math.sin(2 * math.pi * freq * t + phase)

LEG_MAP = [(0,1,2,+1),(4,5,6,+1),(8,9,10,-1),(12,13,14,-1)]

# --- Balance thread ---
def balance_loop():
    global baseline, balance_offset
    recover = False
    while True:
        roll, pitch = get_roll_pitch_angles()
        pitch = -pitch  # flipped
        scale = 2
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
        if a in [0,4,8,12]:
            cmds[a] = baseline[a] - lateral * 0.3

        # Stride + lift
        stride_val = baseline[b] + x_val
        lift_val   = baseline[c] + y_val

        # Height adjustment
        if b and c in [1,2,13,14]:
            stride_val += height*ysign
            lift_val   += height*ysign
        if b and c in [5,6,9,10]:
            stride_val -= height*ysign
            lift_val   -= height*ysign

        # Pitch
        if a == 0: lift_val += pitch
        if a == 4: lift_val -= pitch
        if b == 1: stride_val += pitch
        if b == 5: stride_val -= pitch

        # Roll
        if a == 0: lift_val += roll
        if b == 1: stride_val += roll
        if a == 4: lift_val += roll
        if b == 5: stride_val += roll
        if a == 8: lift_val -= roll
        if b == 9: stride_val -= roll
        if a == 12: lift_val -= roll
        if b == 13: stride_val -= roll

        # Apply balance correction if idle
        if MODE == "stop":
            stride_val += balance_offset.get(b, 0)
            lift_val   += balance_offset.get(c, 0)

        cmds[b] = stride_val
        cmds[c] = lift_val

    set_targets(cmds)

# --- Background walking loop ---
def walking_loop():
    t0 = time.time()
    while True:
        t = time.time() - t0
        if MODE == "walk":
            amp = SPEED
            freq = 4
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

# --- UDP handler ---
def udp_loop():
    global MODE, WALK_TYPE, BACKWARDS, LATERAL, HEIGHT, PITCH, ROLL, SPEED
    global baseline, balance_offset

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            msg = json.loads(data.decode())

            if msg.get("pause"):
                MODE = "stop"
                baseline = pose_protect
                balance_offset = {ch: 0.0 for ch in baseline}
                set_targets(pose_protect)
                continue

            if msg.get("start"):
                MODE = "stop"
                baseline = pose_default
                balance_offset = {ch: 0.0 for ch in baseline}
                set_targets(pose_default)
                continue

            if "mode" in msg: MODE = msg["mode"]
            if "walk_type" in msg: WALK_TYPE = msg["walk_type"]
            if "backwards" in msg: BACKWARDS = bool(msg["backwards"])
            if "lateral" in msg:   LATERAL = int(msg["lateral"])
            if "height" in msg:    HEIGHT = int(msg["height"])
            if "pitch" in msg:     PITCH = int(msg["pitch"])
            if "roll" in msg:      ROLL = int(msg["roll"])
            if "speed" in msg:     SPEED = int(msg["speed"])

        except Exception as e:
            print("⚠️ Bad packet:", e)

# --- Shutdown handler ---
def shutdown_handler(sig, frame):
    print("\n🛑 Caught Ctrl+C, shutting down...")
    kill()
    sys.exit(0)
signal.signal(signal.SIGINT, shutdown_handler)

# --- Main ---
if __name__ == "__main__":
    start_balance_thread()
    threading.Thread(target=walking_loop, daemon=True).start()
    threading.Thread(target=udp_loop, daemon=True).start()
    print(f"🚀 Robot UDP server running on {UDP_IP}:{UDP_PORT}")
    while True:
        time.sleep(1)
