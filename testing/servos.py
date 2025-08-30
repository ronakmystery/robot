from servo_driver import *
import threading, time, random

servos = [
    0, 1, 2, 
    4, 5, 6, 
    8, 9, 10,
    12, 13, 14
]

angles = {
    0: 91,  1: 89,  2: 90,
    4: 102, 5: 80,  6: 85,
    8: 92,  9: 72,  10: 83,
    12: 80, 13: 101, 14: 90
}



targets = angles.copy()

def servo_update(ch, ang):
    set_servo_angle(ch, ang)
    angles[ch] = ang  

ALIVE = True
def servo_worker(ch, speed=5, hz=60):
    period = 1.0 / hz
    while ALIVE:
        cur = angles.get(ch)
        tgt = targets.get(ch)
        if cur != tgt:
            step = max(1, abs(tgt - cur) // speed)
            cur += step if cur < tgt else -step
            servo_update(ch, cur)
        time.sleep(period)

for ch in servos:
    threading.Thread(target=servo_worker, args=(ch,), daemon=True).start()

def set_targets(batch):
    for ch, ang in batch.items():
        targets[ch] = max(0, min(180, int(round(ang))))


def kill():
    print("🔻 Shutting down, releasing servos...")
    for servo in servos:
        pwm.setServoPulse(servo, 0)


