import csv, time
from init import set_servo_angle
from datetime import datetime

# smoothing state
last_vals = {}
ALPHA = 0.2   # smoothing factor (0.1 = very smooth, 1.0 = no smoothing)

def smooth(ch, new):
    prev = last_vals.get(ch, new)
    val = ALPHA * new + (1 - ALPHA) * prev
    last_vals[ch] = val
    return int(round(val))

with open("servo_log.csv") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

prev_time = None
for row in rows:
    try:
        t = datetime.fromisoformat(row["time"])
    except AttributeError:
        t = datetime.strptime(row["time"], "%Y-%m-%dT%H:%M:%S.%f")

    if prev_time is not None:
        delay = (t - prev_time).total_seconds()
        if delay > 0:
            time.sleep(delay)

    prev_time = t

    ch, ang = int(row["channel"]), int(row["angle"])
    ang = smooth(ch, ang)  # <-- smooth before sending
    set_servo_angle(ch, ang)
    print(f"Replayed servo {ch} -> {ang} at {t}")
