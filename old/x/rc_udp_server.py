# server_4legs.py
import socket, threading, time, sys
from init import *  # must provide set_servo_angle, servo_angles, offsets

UDP_IP, UDP_PORT = "0.0.0.0", 5005

# ── FOUR LEGS: RF, LF, RB, LB ─────────────────────────────
ACTIVE = [0,1,2, 4,5,6, 8,9,10, 12,13,14]

# Invert any channels that move the wrong way (knees often need this)
INVERT = {1,2,9,10}   # tweak if roll/pitch directions need flipping

# Per-channel offsets (degrees); keep 0 for pass-through
OFFSET = {ch: 0 for ch in ACTIVE}

# Initialize targets from existing state (or init offsets)
TARGETS = {ch: servo_angles.get(ch, offsets.get(ch)) for ch in ACTIVE}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

last_vals = {}
ALPHA = 0.2
RUNNING = True

def smooth(ch, new):
    prev = last_vals.get(ch, new)
    val = ALPHA * new + (1 - ALPHA) * prev
    last_vals[ch] = val
    return int(round(val))

def clamp(a, lo=0, hi=180):
    return hi if a > hi else lo if a < lo else a

def apply_invert_and_offset(ch, ang):
    if ch in INVERT:
        ang = 180 - ang
    return clamp(ang + OFFSET.get(ch, 0))

def write_servo(ch, ang):
    set_servo_angle(ch, ang)
    servo_angles[ch] = ang

def servo_worker(ch, speed=5, hz=60):
    period = 1.0 / hz
    while RUNNING:
        cur = servo_angles.get(ch, 90)
        tgt = TARGETS[ch]
        if cur != tgt:
            step = max(1, abs(tgt - cur) // speed)
            cur += step if cur < tgt else -step
            write_servo(ch, cur)
        time.sleep(period)

for ch in ACTIVE:
    threading.Thread(target=servo_worker, args=(ch,), daemon=True).start()

print(f"✅ UDP server ready on {UDP_IP}:{UDP_PORT} (channels {ACTIVE})")

def parse_pairs(b):
    # Parse b"ch,ang,ch,ang,..." -> [(ch, ang), ...]
    txt = b.decode(errors="ignore")
    parts = [p.strip() for p in txt.split(",") if p.strip()]
    out, buf = [], []
    for p in parts:
        try:
            buf.append(int(round(float(p))))
            if len(buf) == 2:
                out.append((buf[0], buf[1]))
                buf = []
        except ValueError:
            buf = []  # reset on bad token
    return out

def set_target(ch, raw_ang):
    ang = clamp(smooth(ch, raw_ang))
    ang = apply_invert_and_offset(ch, ang)
    TARGETS[ch] = ang

try:
    while True:
        data, addr = sock.recvfrom(512)
        pairs = parse_pairs(data)
        for ch, ang in pairs:
            if ch in ACTIVE:
                set_target(ch, ang)

except KeyboardInterrupt:
    print("\n🛑 Stopping...")
    RUNNING = False
    time.sleep(0.2)
    sock.close()
    sys.exit(0)
