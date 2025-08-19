import socket, threading, time, csv
from datetime import datetime
from init import set_servo_angle, servo_angles

UDP_IP   = "0.0.0.0"
UDP_PORT = 5005
TARGETS  = {4: 90, 5: 90, 6: 90}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

# ── File logger ─────────────────────────────────────────────
logfile = open("servo_log.csv", "w", newline="")
logwriter = csv.writer(logfile)
logwriter.writerow(["time", "channel", "angle"])  # header

# ── Smoothing ──────────────────────────────────────────────
last_vals = {}
ALPHA = 0.2  # 0.1 = very smooth, 1.0 = raw

def smooth(ch, new):
    prev = last_vals.get(ch, new)
    val = ALPHA * new + (1 - ALPHA) * prev
    last_vals[ch] = val
    return int(round(val))

def servo_worker(ch, speed=5, hz=60):
    """Continuously ease servo toward its target."""
    period = 1.0 / hz
    while True:
        cur = servo_angles.get(ch, 90)
        tgt = TARGETS[ch]
        if cur != tgt:
            step = max(1, abs(tgt - cur) // speed)
            if cur < tgt:
                cur += step
            else:
                cur -= step
            set_servo_angle(ch, cur)
        time.sleep(period)

# Start workers
for ch in TARGETS:
    threading.Thread(target=servo_worker, args=(ch,), daemon=True).start()

print(f"UDP server listening on {UDP_IP}:{UDP_PORT}")

# ── Main loop ──────────────────────────────────────────────
while True:
    data, addr = sock.recvfrom(64)
    try:
        parts = [int(round(float(x))) for x in data.decode().split(",") if x.strip()]
        if len(parts) % 2 != 0:
            parts = parts[:-1]

        for i in range(0, len(parts), 2):
            ch, ang = parts[i], parts[i+1]
            if ch in TARGETS:
                ang = max(0, min(180, ang))     # clamp
                ang = smooth(ch, ang)           # smooth here ✅
                TARGETS[ch] = ang
                logwriter.writerow([datetime.now().isoformat(), ch, ang])
                logfile.flush()
        print("Targets:", TARGETS)
    except Exception as e:
        print("Bad packet:", e)
