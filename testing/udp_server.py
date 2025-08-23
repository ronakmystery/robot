import socket, threading, time, csv
from datetime import datetime
from init import *

UDP_IP, UDP_PORT = "0.0.0.0", 5005

# Channels:
# Front Left  : 0 (roll), 1 (femur), 2 (knee)
# Front Right : 4 (roll), 5 (femur), 6 (knee)
# Back  Left  : 8 (roll), 9 (femur), 10 (knee)  ← mirror of 0,1,2
# Back  Right : 12 (roll),13 (femur),14 (knee)  ← mirror of 4,5,6
ACTIVE  = [
    0,1,2,
    4,5,6,
    8,9,10,
    12,13,14]

# Your current inversion set:
INVERT  = {0, 12,5,13,6,14,1,9}

# Optional per-channel trims
OFFSET  = {ch: 0 for ch in ACTIVE}

# Mirroring map (front → back)
MIRROR_LINKS = {0:[8], 1:[9], 2:[10], 4:[12], 5:[13], 6:[14]}

TARGETS = {ch: servo_angles.get(ch, offsets.get(ch)) for ch in ACTIVE}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

logfile = open("servo_log.csv", "w", newline="")
logwriter = csv.writer(logfile)
logwriter.writerow(["time", "channel", "angle", "source"])

last_vals = {}
ALPHA = 0.2

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
    ang = clamp(ang + OFFSET.get(ch, 0))
    return ang

def write_servo(ch, ang):
    set_servo_angle(ch, ang)
    servo_angles[ch] = ang

def servo_worker(ch, speed=1, hz=60):
    period = 1.0 / hz
    while True:
        cur = servo_angles.get(ch, 90)
        tgt = TARGETS[ch]
        if cur != tgt:
            step = max(1, abs(tgt - cur) // speed)
            cur += step if cur < tgt else -step
            write_servo(ch, cur)
        time.sleep(period)

for ch in ACTIVE:
    threading.Thread(target=servo_worker, args=(ch,), daemon=True).start()

print(f"✅ UDP server on {UDP_IP}:{UDP_PORT}")
print(f"🦴 Active: {ACTIVE}")
print(f"↔️  Inverted: {sorted(list(INVERT))}")
print(f"🔁 Mirrors: {MIRROR_LINKS}")
print(f"🎯 Offsets: {OFFSET}")

def parse_pairs(b):
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
            buf = []
    return out

def set_targets_with_mirrors(ch, raw_ang, src_addr):
    """
    Compute FINAL angle for the source channel,
    then for each mirror channel RECOMPUTE from the same raw input
    so the mirror's own invert/offset rules (e.g., for 8 and 12) apply.
    """
    # source channel
    ang_src = clamp(smooth(ch, raw_ang))
    ang_src = apply_invert_and_offset(ch, ang_src)
    TARGETS[ch] = ang_src
    logwriter.writerow([datetime.now().isoformat(), ch, ang_src, src_addr])

    # mirrors: recompute per mirror channel (fixes 8 & 12 inversion)
    for m_ch in MIRROR_LINKS.get(ch, []):
        ang_m = clamp(smooth(m_ch, raw_ang))
        ang_m = apply_invert_and_offset(m_ch, ang_m)
        TARGETS[m_ch] = ang_m
        logwriter.writerow([datetime.now().isoformat(), m_ch, ang_m, src_addr])

while True:
    data, addr = sock.recvfrom(256)
    try:
        pairs = parse_pairs(data)
        updated = False
        for ch, ang in pairs:
            if ch in ACTIVE:
                set_targets_with_mirrors(ch, ang, f"{addr[0]}:{addr[1]}")
                updated = True
        if updated:
            logfile.flush()
            print("🎯", TARGETS)
    except Exception as e:
        print("⚠️ Bad packet:", e)
