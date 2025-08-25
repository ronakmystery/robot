import socket, threading, time, csv, sys
from datetime import datetime
from init import *

UDP_IP, UDP_PORT = "0.0.0.0", 5005

# All 4 legs: 0-2 RF, 4-6 LF, 8-10 RB, 12-14 LB
ACTIVE = [0,1,2, 4,5,6, 8,9,10, 12,13,14]

INVERT = {0,1, 5,6,10, 12}
OFFSET = {ch: 0 for ch in ACTIVE}
MIRROR_LINKS = {0:[8], 1:[9], 2:[10], 4:[12], 5:[13], 6:[14]}

TARGETS = {ch: servo_angles.get(ch, offsets.get(ch)) for ch in ACTIVE}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

logfile = open("servo_log.csv", "w", newline="")
logwriter = csv.writer(logfile)
logwriter.writerow(["time", "channel", "angle", "source"])

last_vals = {}
ALPHA = 0.2
RUNNING = True   # <-- global flag

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

def servo_worker(ch, speed=1, hz=60):
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
    ang_src = clamp(smooth(ch, raw_ang))
    ang_src = apply_invert_and_offset(ch, ang_src)
    TARGETS[ch] = ang_src
    logwriter.writerow([datetime.now().isoformat(), ch, ang_src, src_addr])

    for m_ch in MIRROR_LINKS.get(ch, []):
        ang_m = clamp(smooth(m_ch, raw_ang))
        ang_m = apply_invert_and_offset(m_ch, ang_m)
        TARGETS[m_ch] = ang_m
        logwriter.writerow([datetime.now().isoformat(), m_ch, ang_m, src_addr])

try:
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

except KeyboardInterrupt:
    print("\n🛑 Stopping...")
    RUNNING = False
    time.sleep(0.2)   # give threads time to exit
    logfile.close()
    sock.close()
    sys.exit(0)
